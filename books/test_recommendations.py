import io
import json
from urllib.error import HTTPError, URLError
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Book
from .recommendations import (
    DISCLAIMER, GMS_RESPONSES_URL, MAX_RESPONSE_BYTES, MODEL, RecommendationError,
    build_request_data, recommend_books, validate_recommendations,
)


def liked_data():
    return [{'title': '모모', 'author': '미하엘 엔데', 'category': '어린이·청소년', 'description': '시간과 우정의 이야기'}]


def recommendation(title='끝없는 이야기', author='미하엘 엔데'):
    return {'title': title, 'author': author, 'category': '소설',
            'description': '현실과 환상을 넘나드는 이야기', 'reason': '좋아요한 책의 상상력과 주제를 이어갈 수 있어요.'}


def response_body(items=None):
    return {'status': 'completed', 'output': [
        {'type': 'reasoning', 'summary': []},
        {'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps({
            'recommendations': [recommendation()] if items is None else items,
        }, ensure_ascii=False)}]},
    ]}


@override_settings(GMS_KEY='test-server-only-key')
class RecommendationServiceTests(TestCase):
    def mock_response(self, data):
        context = MagicMock()
        context.__enter__.return_value.read.return_value = (
            data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode('utf-8')
        )
        return context

    @patch('books.recommendations.urlopen')
    def test_gms_receives_structured_request_and_returns_validated_books(self, mocked):
        mocked.return_value = self.mock_response(response_body())
        result = recommend_books(liked_data())
        self.assertEqual(result, [recommendation()])
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, GMS_RESPONSES_URL)
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(request.get_header('Authorization'), 'Bearer test-server-only-key')
        payload = json.loads(request.data)
        self.assertEqual(payload['model'], MODEL)
        self.assertFalse(payload['store'])
        self.assertEqual(payload['text']['format']['type'], 'json_schema')
        self.assertTrue(payload['text']['format']['strict'])
        self.assertEqual(json.loads(payload['input'][0]['content']), build_request_data(liked_data()))
        self.assertNotIn('test-server-only-key', payload['input'][0]['content'])
        self.assertEqual(mocked.call_args.kwargs['timeout'], 60)

    def test_payload_only_contains_book_fields_and_bounds_descriptions(self):
        data = liked_data()
        data[0].update(description='x' * 1000, username='private-user', email='private@example.com')
        payload = build_request_data(data)
        self.assertEqual(set(payload), {'liked_books', 'recommend_count'})
        self.assertEqual(set(payload['liked_books'][0]), {'title', 'author', 'category', 'description'})
        self.assertEqual(len(payload['liked_books'][0]['description']), 400)
        self.assertNotIn('private', json.dumps(payload))

    def test_liked_titles_and_duplicate_recommendations_are_filtered(self):
        data = {'recommendations': [recommendation(' 모 모 ', '다른 표기'), recommendation(), recommendation()]}
        self.assertEqual(validate_recommendations(data, liked_data()), [recommendation()])
        with self.assertRaises(RecommendationError):
            validate_recommendations({'recommendations': [recommendation('모모')]}, liked_data())

    def test_invalid_schemas_are_rejected(self):
        cases = [None, [], {}, {'recommendations': []}, {'recommendations': 'invalid'},
                 {'recommendations': [recommendation()] * 4}, {'recommendations': [None]},
                 {'recommendations': [{'title': '누락'}]}, {'recommendations': [recommendation()], 'extra': True}]
        for field, value in [('title', ''), ('title', 'x' * 201), ('author', 1), ('category', None), ('reason', ' '), ('description', [])]:
            item = recommendation()
            item[field] = value
            cases.append({'recommendations': [item]})
        for data in cases:
            with self.subTest(data=data), self.assertRaises(RecommendationError):
                validate_recommendations(data, liked_data())

    @patch('books.recommendations.urlopen')
    def test_missing_credentials_do_not_call_api(self, mocked):
        for key in ['', 'your-gms-api-key']:
            with self.subTest(key=key), override_settings(GMS_KEY=key):
                with self.assertRaises(RecommendationError) as error:
                    recommend_books(liked_data())
                self.assertEqual(error.exception.status, 503)
        mocked.assert_not_called()

    @patch('books.recommendations.urlopen')
    def test_refusal_incomplete_empty_and_malformed_responses_are_rejected(self, mocked):
        cases = [
            {'status': 'incomplete', 'output': []}, {'status': 'completed', 'output': []},
            {'status': 'completed', 'output': 'invalid'},
            {'status': 'completed', 'output': [{'type': 'message', 'content': 'invalid'}]},
            {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'refused'}]}]},
            {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'not json'}]}]},
            b'not-json', b'\xff', b'x' * (MAX_RESPONSE_BYTES + 1),
        ]
        for data in cases:
            with self.subTest(data_type=type(data).__name__):
                mocked.return_value = self.mock_response(data)
                with self.assertRaises(RecommendationError):
                    recommend_books(liked_data())

    @patch('books.recommendations.urlopen')
    def test_network_and_http_errors_are_safe_and_do_not_retry(self, mocked):
        cases = [
            (TimeoutError('private error details'), 504),
            (URLError(TimeoutError('private error details')), 504),
            (URLError('private error details'), 502),
            (HTTPError(GMS_RESPONSES_URL, 401, 'private error details', {}, io.BytesIO(b'private body')), 503),
            (HTTPError(GMS_RESPONSES_URL, 429, 'private error details', {}, io.BytesIO(b'private body')), 503),
            (HTTPError(GMS_RESPONSES_URL, 500, 'private error details', {}, io.BytesIO(b'private body')), 502),
        ]
        for exception, status in cases:
            with self.subTest(exception=type(exception).__name__):
                mocked.reset_mock()
                mocked.side_effect = exception
                with self.assertRaises(RecommendationError) as result:
                    recommend_books(liked_data())
                self.assertEqual(result.exception.status, status)
                self.assertNotIn('private', str(result.exception))
                self.assertNotIn('test-server-only-key', str(result.exception))
                mocked.assert_called_once()


@override_settings(GMS_KEY='test-server-only-key')
class RecommendationViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user('recommend_alice', password='Reader!Test2026')
        cls.bob = User.objects.create_user('recommend_bob', password='Reader!Test2026')
        cls.book = Book.objects.create(title='모모', author='미하엘 엔데', description='시간 이야기', customer_review_rank='9.0')
        cls.other = Book.objects.create(title='다른 사람의 책', author='다른 작가', description='소개', customer_review_rank='8.0')
        cls.registered = Book.objects.create(title='끝없는 이야기', author='미하엘 엔데', description='환상 이야기', customer_review_rank='9.0')
        cls.book.liked_users.add(cls.alice)
        cls.other.liked_users.add(cls.bob)

    def setUp(self):
        cache.clear()
        self.client.force_login(self.alice)
        self.url = reverse('books:recommendations')

    def tearDown(self):
        cache.clear()

    @patch('books.views.recommend_books')
    def test_endpoint_uses_only_current_users_likes_and_links_registered_books(self, mocked):
        mocked.return_value = [recommendation(), recommendation('새로운 외부 도서', '외부 저자')]
        before = Book.objects.count()
        response = self.client.post(self.url, {'user_id': self.bob.pk, 'liked_books': 'forged'})
        self.assertEqual(response.status_code, 200)
        sent = mocked.call_args.args[0]
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]['title'], '모모')
        self.assertEqual(set(sent[0]), {'title', 'author', 'category', 'description'})
        data = response.json()
        self.assertEqual(data['liked_count'], 1)
        self.assertEqual(data['disclaimer'], DISCLAIMER)
        self.assertEqual(data['recommendations'][0]['detail_url'], self.registered.get_absolute_url())
        self.assertIsNone(data['recommendations'][1]['detail_url'])
        self.assertEqual(Book.objects.count(), before)
        self.assertIn('no-store', response['Cache-Control'])

    @patch('books.views.recommend_books')
    def test_repeated_requests_are_throttled_without_extending_window(self, mocked):
        mocked.side_effect = lambda data: [recommendation()]
        with patch('books.views.time.time', return_value=1000):
            self.assertEqual(self.client.post(self.url).status_code, 200)
        with patch('books.views.time.time', return_value=1010):
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response['Retry-After'], '20')
        with patch('books.views.time.time', return_value=1031):
            self.assertEqual(self.client.post(self.url).status_code, 200)
        self.assertEqual(mocked.call_count, 2)

    @patch('books.views.recommend_books')
    def test_throttle_is_per_user(self, mocked):
        mocked.side_effect = lambda data: [recommendation()]
        self.assertEqual(self.client.post(self.url).status_code, 200)
        self.client.force_login(self.bob)
        self.assertEqual(self.client.post(self.url).status_code, 200)
        self.assertEqual(mocked.call_count, 2)

    @patch('books.views.recommend_books')
    def test_in_progress_request_cannot_be_duplicated(self, mocked):
        busy_key = f'book-recommendations:{self.alice.pk}:busy'
        cache.set(busy_key, True, timeout=90)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 429)
        self.assertTrue(cache.get(busy_key))
        mocked.assert_not_called()

    @patch('books.views.recommend_books')
    def test_api_failure_releases_busy_lock_and_keeps_cooldown(self, mocked):
        mocked.side_effect = RecommendationError('안전한 오류 메시지', status=504)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()['error'], '안전한 오류 메시지')
        self.assertIsNone(cache.get(f'book-recommendations:{self.alice.pk}:busy'))
        self.assertEqual(self.client.post(self.url).status_code, 429)
        mocked.assert_called_once()

    @patch('books.views.recommend_books')
    def test_empty_likes_do_not_call_api(self, mocked):
        self.alice.liked_books.clear()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        mocked.assert_not_called()

    @patch('books.views.recommend_books')
    def test_authentication_methods_and_csrf(self, mocked):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.put(self.url).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.post(self.url).status_code, 401)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.alice)
        self.assertEqual(csrf_client.post(self.url).status_code, 403)
        mocked.assert_not_called()

    @patch('books.views.recommend_books')
    def test_button_and_disclaimer_only_appear_in_liked_page_without_api_calls(self, mocked):
        response = self.client.get(reverse('books:index'), {'liked': '1'})
        self.assertContains(response, 'data-recommendation-form')
        self.assertContains(response, 'data-throttle-seconds="30"')
        self.assertContains(response, DISCLAIMER)
        self.assertNotContains(response, 'test-server-only-key')
        self.assertNotContains(self.client.get(reverse('books:index')), 'data-recommendation-form')
        mocked.assert_not_called()
