from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from books.models import Category


class InterestCategoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user('interest_alice', password='Reader!Test2026', email='alice@example.com', interested_genres='NOVEL')
        cls.bob = User.objects.create_user('interest_bob', password='Reader!Test2026')
        cls.novel, _ = Category.objects.get_or_create(name='소설')
        cls.essay, _ = Category.objects.get_or_create(name='에세이')
        cls.bob.interested_categories.add(cls.essay)

    def test_profile_can_save_multiple_interests_for_current_user_only(self):
        self.client.force_login(self.alice)
        response = self.client.post(reverse('accounts:update_interested_categories'), {
            'interested_categories': [self.novel.pk, self.essay.pk], 'user_id': self.bob.pk,
            'email': 'should-not-change@example.com', 'is_staff': 'on',
        })
        self.assertRedirects(response, reverse('accounts:profile', args=[self.alice.username]))
        self.assertCountEqual(self.alice.interested_categories.all(), [self.novel, self.essay])
        self.assertEqual(list(self.bob.interested_categories.all()), [self.essay])
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.email, 'alice@example.com')
        self.assertEqual(self.alice.interested_genres, 'NOVEL')
        self.assertFalse(self.alice.is_staff)

    def test_interests_are_preselected_and_link_to_category_pages(self):
        self.alice.interested_categories.add(self.novel)
        self.client.force_login(self.alice)
        response = self.client.get(reverse('accounts:profile', args=[self.alice.username]))
        self.assertEqual(response.context['interest_form'].initial['interested_categories'], [self.novel])
        self.assertContains(response, self.novel.get_absolute_url())
        self.assertContains(response, '관심 카테고리 저장')
        response = self.client.get(reverse('accounts:update'))
        self.assertEqual(response.context['form'].initial['interested_categories'], [self.novel])

    def test_interests_can_be_cleared(self):
        self.alice.interested_categories.add(self.novel)
        self.client.force_login(self.alice)
        self.client.post(reverse('accounts:update_interested_categories'), {})
        self.assertFalse(self.alice.interested_categories.exists())

    def test_invalid_interests_do_not_erase_saved_choices(self):
        self.alice.interested_categories.add(self.novel)
        self.client.force_login(self.alice)
        for value in ['999999', 'invalid']:
            response = self.client.post(reverse('accounts:update_interested_categories'), {'interested_categories': [value]})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['interest_form'].errors)
            self.assertEqual(list(self.alice.interested_categories.all()), [self.novel])

    def test_other_users_profiles_have_no_interest_edit_form(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse('accounts:profile', args=[self.bob.username]))
        self.assertContains(response, self.essay.get_absolute_url())
        self.assertNotContains(response, f'action="{reverse("accounts:update_interested_categories")}"')

    def test_interest_update_requires_login_post_and_csrf(self):
        url = reverse('accounts:update_interested_categories')
        self.assertEqual(self.client.post(url, {}).status_code, 302)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.put(url).status_code, 405)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        self.assertEqual(client.post(url, {'interested_categories': [self.novel.pk]}).status_code, 403)

    def test_signup_can_save_interest_categories(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'new_category_reader', 'password1': 'Reader!Garden2026', 'password2': 'Reader!Garden2026',
            'interested_categories': [self.novel.pk, self.essay.pk],
        })
        self.assertRedirects(response, reverse('books:index'))
        user = get_user_model().objects.get(username='new_category_reader')
        self.assertCountEqual(user.interested_categories.all(), [self.novel, self.essay])

    def test_full_account_update_can_save_interest_categories(self):
        self.client.force_login(self.alice)
        response = self.client.post(reverse('accounts:update'), {
            'email': 'updated@example.com', 'interested_categories': [self.novel.pk],
        })
        self.assertRedirects(response, reverse('books:index'))
        self.assertEqual(list(self.alice.interested_categories.all()), [self.novel])
