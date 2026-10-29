from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from .models import Book


class BookFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('reader', password='Reader!Test2026')
        cls.book = Book.objects.create(
            title='테스트 도서', description='책 소개\n두 번째 문장',
            author='테스트 작가', customer_review_rank=Decimal('8.5'),
        )

    def data(self, **changes):
        data = {'title': '새 도서', 'description': '도서 설명', 'author': '새 작가', 'customer_review_rank': '9.1', 'category': self.book.category_id}
        data.update(changes)
        return data

    def test_public_list_and_detail_show_all_book_fields(self):
        response = self.client.get(reverse('books:index'))
        self.assertContains(response, self.book.title)
        self.assertNotContains(response, reverse('books:create'))
        response = self.client.get(self.book.get_absolute_url())
        for value in [self.book.title, self.book.author, '8.5', '두 번째 문장']:
            self.assertContains(response, value)
        self.assertNotContains(response, reverse('books:delete', args=[self.book.pk]))

    def test_search_by_title_and_author(self):
        for keyword in ['테스트 도서', '테스트 작가']:
            self.assertContains(self.client.get(reverse('books:index'), {'q': keyword}), self.book.title)
        response = self.client.get(reverse('books:index'), {'q': '없는도서'})
        self.assertContains(response, '검색 결과가 없습니다')

    def test_anonymous_users_cannot_write(self):
        for name, args in [('create', []), ('update', [self.book.pk]), ('delete', [self.book.pk])]:
            url = reverse(f'books:{name}', args=args)
            response = self.client.post(url, self.data())
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse('accounts:login')))
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, '테스트 도서')
        self.assertEqual(Book.objects.count(), 1)

    def test_authenticated_create_update_delete_flow(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('books:create')).status_code, 200)
        response = self.client.post(reverse('books:create'), self.data())
        book = Book.objects.get(title='새 도서')
        self.assertRedirects(response, book.get_absolute_url())
        url = reverse('books:update', args=[book.pk])
        self.assertContains(self.client.get(url), '새 도서')
        response = self.client.post(url, self.data(title='수정 도서', customer_review_rank='10.0'))
        self.assertRedirects(response, book.get_absolute_url())
        book.refresh_from_db()
        self.assertEqual(book.title, '수정 도서')
        self.assertEqual(book.customer_review_rank, Decimal('10.0'))
        response = self.client.post(reverse('books:delete', args=[book.pk]))
        self.assertRedirects(response, reverse('books:index'))
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_invalid_book_fields_are_rejected(self):
        self.client.force_login(self.user)
        for changes in [
            {'title': ''}, {'title': 'x' * 201}, {'author': ''}, {'description': ''},
            {'customer_review_rank': '-0.1'}, {'customer_review_rank': '10.1'},
            {'customer_review_rank': '1.11'}, {'customer_review_rank': 'invalid'},
        ]:
            with self.subTest(changes=changes):
                response = self.client.post(reverse('books:create'), self.data(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
        self.assertEqual(Book.objects.count(), 1)

    def test_invalid_update_preserves_database(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('books:update', args=[self.book.pk]), self.data(title='', customer_review_rank='99'))
        self.assertEqual(response.status_code, 200)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, '테스트 도서')

    def test_rating_database_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Book.objects.create(title='잘못된 평점', author='작가', description='설명', customer_review_rank=11)

    def test_http_method_restrictions(self):
        self.client.force_login(self.user)
        for method, url in [
            ('post', '/'),
            ('post', reverse('books:index')), ('post', self.book.get_absolute_url()),
            ('get', reverse('books:delete', args=[self.book.pk])),
            ('put', reverse('books:create')), ('patch', reverse('books:update', args=[self.book.pk])),
        ]:
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(self.client, method)(url).status_code, 405)

    def test_missing_books_return_404(self):
        self.client.force_login(self.user)
        for name in ['detail', 'update', 'delete']:
            url = reverse(f'books:{name}', args=[99999])
            response = self.client.post(url) if name == 'delete' else self.client.get(url)
            self.assertEqual(response.status_code, 404)

    def test_csrf_protects_writes(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(reverse('books:delete', args=[self.book.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_local_bootstrap_script_has_executable_mime_type(self):
        from django.contrib.staticfiles.views import serve
        response = serve(RequestFactory().get('/static/vendor/bootstrap.bundle.min.js'),
                         'vendor/bootstrap.bundle.min.js', insecure=True)
        try:
            self.assertEqual(response.status_code, 200)
            self.assertIn(response['Content-Type'].split(';')[0],
                          ['text/javascript', 'application/javascript'])
        finally:
            response.close()


class PersonalBookLikeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user('alice', password='Reader!Test2026')
        cls.bob = User.objects.create_user('bob', password='Reader!Test2026')
        cls.book = Book.objects.create(title='나의 책', description='소개', author='작가', customer_review_rank='8.0')
        cls.other_book = Book.objects.create(title='다른 책', description='소개', author='다른 작가', customer_review_rank='9.0')

    def like(self, liked, **data):
        return self.client.post(reverse('books:like', args=[self.book.pk]),
                                {'liked': liked, **data}, HTTP_ACCEPT='application/json')

    def test_books_start_without_likes(self):
        self.assertFalse(self.book.liked_users.exists())
        self.client.force_login(self.alice)
        response = self.client.get(self.book.get_absolute_url())
        self.assertFalse(response.context['book'].is_liked)
        self.assertContains(response, 'aria-pressed="false"')

    def test_likes_are_personal_and_repeated_requests_are_idempotent(self):
        self.client.force_login(self.alice)
        for _ in range(2):
            response = self.like('true', user_id=self.bob.pk)
            self.assertEqual(response.json(), {'book_id': self.book.pk, 'liked': True})
        self.assertEqual(list(self.book.liked_users.all()), [self.alice])
        self.client.force_login(self.bob)
        self.like('true')
        self.client.force_login(self.alice)
        for _ in range(2):
            self.assertFalse(self.like('false').json()['liked'])
        self.assertFalse(self.alice.liked_books.exists())
        self.assertTrue(self.bob.liked_books.filter(pk=self.book.pk).exists())

    def test_only_current_users_books_appear_in_filtered_query(self):
        self.book.liked_users.add(self.alice)
        self.other_book.liked_users.add(self.bob)
        self.client.force_login(self.alice)
        response = self.client.get(reverse('books:index'), {'liked': '1'})
        self.assertEqual(list(response.context['books']), [self.book])
        self.assertContains(response, '내가 좋아요한 책')
        self.assertContains(response, 'aria-pressed="true"')
        self.assertEqual(response.context['total_count'], 1)
        self.client.force_login(self.bob)
        response = self.client.get(reverse('books:index'), {'liked': '1'})
        self.assertEqual(list(response.context['books']), [self.other_book])

    def test_filtered_search_preserves_personal_filter(self):
        self.book.liked_users.add(self.alice)
        self.client.force_login(self.alice)
        response = self.client.get(reverse('books:index'), {'liked': '1', 'q': '나의'})
        self.assertEqual(list(response.context['books']), [self.book])
        self.assertContains(response, 'name="liked" value="1"')
        response = self.client.get(reverse('books:index'), {'liked': '1', 'q': '다른'})
        self.assertEqual(list(response.context['books']), [])

    def test_empty_personal_list_has_guidance(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse('books:index'), {'liked': '1'})
        self.assertContains(response, '아직 좋아요한 책이 없어요')

    def test_anonymous_requests_cannot_read_or_write_personal_likes(self):
        response = self.like('true')
        self.assertEqual(response.status_code, 401)
        self.assertFalse(self.book.liked_users.exists())
        response = self.client.get(reverse('books:index'), {'liked': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('accounts:login')))

    def test_like_endpoint_enforces_methods_validation_and_missing_book(self):
        self.client.force_login(self.alice)
        url = reverse('books:like', args=[self.book.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.put(url).status_code, 405)
        for value in ['', 'invalid', '1']:
            self.assertEqual(self.like(value).status_code, 400)
        self.assertEqual(self.client.post(url).status_code, 400)
        self.assertFalse(self.book.liked_users.exists())
        self.assertEqual(self.client.post(reverse('books:like', args=[99999]), {'liked': 'true'}).status_code, 404)

    def test_like_endpoint_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        response = client.post(reverse('books:like', args=[self.book.pk]), {'liked': 'true'})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.book.liked_users.exists())

    def test_like_state_is_rendered_for_each_user_without_extra_queries(self):
        from .views import books_with_like_state
        self.book.liked_users.add(self.alice)
        with self.assertNumQueries(1):
            states = {book.pk: book.is_liked for book in books_with_like_state(self.alice)}
        self.assertEqual(states, {self.book.pk: True, self.other_book.pk: False})
        self.client.force_login(self.bob)
        response = self.client.get(self.book.get_absolute_url())
        self.assertFalse(response.context['book'].is_liked)
        self.client.force_login(self.alice)
        response = self.client.get(self.book.get_absolute_url())
        self.assertTrue(response.context['book'].is_liked)

    def test_non_javascript_form_submission_redirects_to_detail(self):
        self.client.force_login(self.alice)
        response = self.client.post(reverse('books:like', args=[self.book.pk]), {'liked': 'true'})
        self.assertRedirects(response, self.book.get_absolute_url())
        self.assertTrue(self.book.liked_users.filter(pk=self.alice.pk).exists())

    def test_deleting_user_cleans_up_only_their_likes(self):
        self.book.liked_users.add(self.alice, self.bob)
        self.alice.delete()
        self.assertEqual(list(self.book.liked_users.all()), [self.bob])
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())
