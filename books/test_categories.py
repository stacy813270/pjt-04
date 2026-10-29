from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from .models import Book, Category


class CategoryFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('category_reader', password='Reader!Test2026')
        cls.novel, _ = Category.objects.get_or_create(name='소설')
        cls.essay, _ = Category.objects.get_or_create(name='에세이')
        cls.book = Book.objects.create(title='소설책', description='소개', author='소설 작가', customer_review_rank='9.0', category=cls.novel)
        cls.other = Book.objects.create(title='에세이책', description='소개', author='다른 작가', customer_review_rank='8.0', category=cls.essay)

    def data(self, **changes):
        data = {'title': '추가 도서', 'description': '책 소개', 'author': '작가', 'customer_review_rank': '9.2', 'category': self.novel.pk}
        data.update(changes)
        return data

    def test_category_list_only_returns_matching_books(self):
        response = self.client.get(self.novel.get_absolute_url())
        self.assertEqual(list(response.context['books']), [self.book])
        self.assertEqual(response.context['selected_category'], self.novel)
        self.assertContains(response, '소설책')
        self.assertNotContains(response, '에세이책')
        self.assertContains(response, f'action="{self.novel.get_absolute_url()}"')
        self.assertEqual(self.client.get(reverse('books:category', args=[999999])).status_code, 404)
        self.assertEqual(self.client.post(self.novel.get_absolute_url()).status_code, 405)

    def test_categories_search_and_likes_work_together(self):
        self.book.liked_users.add(self.user)
        self.other.liked_users.add(self.user)
        self.client.force_login(self.user)
        response = self.client.get(self.novel.get_absolute_url(), {'liked': '1', 'q': '소설'})
        self.assertEqual(list(response.context['books']), [self.book])
        self.assertContains(response, 'name="liked" value="1"')
        self.assertContains(response, self.essay.get_absolute_url() + '?liked=1&amp;q=')
        self.assertContains(response, self.novel.get_absolute_url() + '?liked=1')
        response = self.client.get(self.novel.get_absolute_url(), {'q': '에세이'})
        self.assertEqual(list(response.context['books']), [])

    def test_sidebar_counts_global_books_and_includes_empty_categories(self):
        empty = Category.objects.create(name='비어 있는 카테고리')
        response = self.client.get(reverse('books:index'))
        counts = {category.pk: category.book_count for category in response.context['sidebar_categories']}
        self.assertEqual(counts[self.novel.pk], 1)
        self.assertEqual(counts[self.essay.pk], 1)
        self.assertEqual(counts[empty.pk], 0)
        self.assertEqual(response.context['category_book_total'], 2)
        self.assertContains(response, empty.get_absolute_url())
        self.assertContains(self.client.get(empty.get_absolute_url()), '이 카테고리에 등록된 책이 없어요')

    def test_authenticated_user_can_create_and_change_category(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('books:create'), self.data())
        book = Book.objects.get(title='추가 도서')
        self.assertRedirects(response, book.get_absolute_url())
        self.assertEqual(book.category, self.novel)
        book.liked_users.add(self.user)
        url = reverse('books:update', args=[book.pk])
        self.assertEqual(self.client.get(url).context['form'].initial['category'], self.novel.pk)
        self.assertRedirects(self.client.post(url, self.data(category=self.essay.pk)), book.get_absolute_url())
        book.refresh_from_db()
        self.assertEqual(book.category, self.essay)
        self.assertTrue(book.liked_users.filter(pk=self.user.pk).exists())

    def test_new_category_can_be_created_with_book(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('books:create'), self.data(category='', new_category='  컴퓨터   IT  '))
        book = Book.objects.get(title='추가 도서')
        self.assertRedirects(response, book.get_absolute_url())
        self.assertEqual(book.category.name, '컴퓨터 IT')
        self.assertContains(self.client.get(book.get_absolute_url()), '컴퓨터 IT')

    def test_new_category_takes_precedence_during_update(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('books:update', args=[self.book.pk]), self.data(new_category='여행'))
        self.book.refresh_from_db()
        self.assertRedirects(response, self.book.get_absolute_url())
        self.assertEqual(self.book.category.name, '여행')

    def test_duplicate_new_name_reuses_existing_category(self):
        existing = Category.objects.create(name='Computer IT')
        self.client.force_login(self.user)
        before = Category.objects.count()
        self.client.post(reverse('books:create'), self.data(new_category='  computer   it  '))
        self.assertEqual(Book.objects.get(title='추가 도서').category, existing)
        self.assertEqual(Category.objects.count(), before)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Category.objects.create(name='COMPUTER IT')

    def test_invalid_book_does_not_create_category(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('books:create'), self.data(title='', new_category='생성되면 안 됨'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(Category.objects.filter(name='생성되면 안 됨').exists())

    def test_missing_category_and_invalid_choices_are_rejected(self):
        self.client.force_login(self.user)
        for changes in [{'category': ''}, {'category': '999999'}, {'category': 'invalid'}, {'new_category': 'x' * 51}]:
            with self.subTest(changes=changes):
                response = self.client.post(reverse('books:create'), self.data(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
        self.assertEqual(Book.objects.count(), 2)

    def test_category_cannot_be_deleted_while_books_use_it(self):
        with self.assertRaises(ProtectedError):
            self.novel.delete()

    def test_anonymous_user_cannot_create_category(self):
        response = self.client.post(reverse('books:create'), self.data(new_category='비로그인 생성'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(name='비로그인 생성').exists())

    def test_seed_books_provides_categories_and_preserves_existing_data(self):
        from io import StringIO
        call_command('seed_books', stdout=StringIO())
        book = Book.objects.get(title='모모')
        self.assertEqual(book.category.name, '어린이·청소년')
        book.description = '사용자가 수정한 설명'
        book.category = self.essay
        book.save()
        call_command('seed_books', stdout=StringIO())
        book.refresh_from_db()
        self.assertEqual(book.description, '사용자가 수정한 설명')
        self.assertEqual(book.category, self.essay)


class CategoryDataMigrationTests(TransactionTestCase):
    def test_existing_books_are_backfilled_without_losing_data_or_likes(self):
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        before = [('books', '0002_book_liked_users'), ('accounts', '0001_initial')]
        try:
            executor.migrate(before)
            old_apps = executor.loader.project_state(before).apps
            OldBook = old_apps.get_model('books', 'Book')
            OldUser = old_apps.get_model('accounts', 'User')
            user = OldUser.objects.create(username='migration_reader')
            titles = ['어린 왕자', '모모', '데미안', '오만과 편견', '동물 농장', '월든', '판단 불가 도서']
            for title in titles:
                book = OldBook.objects.create(title=title, author='작가', description='보존할 설명', customer_review_rank='9.0')
                book.liked_users.add(user)
            MigrationExecutor(connection).migrate(targets)
            expected = ['어린이·청소년', '어린이·청소년', '소설', '소설', '소설', '에세이', '기타']
            for title, category in zip(titles, expected):
                book = Book.objects.get(title=title)
                self.assertEqual(book.category.name, category)
                self.assertEqual(book.description, '보존할 설명')
                self.assertTrue(book.liked_users.filter(pk=user.pk).exists())
            self.assertFalse(Book.objects.filter(category__isnull=True).exists())
        finally:
            MigrationExecutor(connection).migrate(targets)
