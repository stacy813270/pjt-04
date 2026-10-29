from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from .forms import CustomUserChangeForm, CustomUserCreationForm

User = get_user_model()


class AccountFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'Reading!Garden2026'
        cls.user = User.objects.create_user(
            'existing_reader', password=cls.password, email='reader@example.com',
            interested_genres='NOVEL,SCIENCE',
        )

    def signup_data(self, **changes):
        data = {
            'username': 'new_reader', 'password1': 'Books!Forest2026', 'password2': 'Books!Forest2026',
            'email': 'new@example.com', 'last_name': '김', 'first_name': '독서', 'gender': 'N',
            'age': 24, 'weekly_reading_hours': 5, 'annual_reading_count': 12,
            'interested_genres': ['NOVEL', 'ESSAY'],
        }
        data.update(changes)
        return data

    def test_signup_logs_in_and_serializes_genres(self):
        self.assertEqual(self.client.get(reverse('accounts:signup')).status_code, 200)
        response = self.client.post(reverse('accounts:signup'), self.signup_data())
        self.assertRedirects(response, reverse('books:index'))
        user = User.objects.get(username='new_reader')
        self.assertEqual(user.interested_genres, 'NOVEL,ESSAY')
        self.assertTrue(user.check_password('Books!Forest2026'))
        self.assertEqual(self.client.session[SESSION_KEY], str(user.pk))

    def test_signup_optional_reading_fields_can_be_empty(self):
        response = self.client.post(reverse('accounts:signup'), self.signup_data(
            age='', weekly_reading_hours='', annual_reading_count='', interested_genres=[],
        ))
        self.assertRedirects(response, reverse('books:index'))
        self.assertEqual(User.objects.get(username='new_reader').interested_genres, '')

    def test_signup_validation(self):
        for changes in [
            {'username': 'existing_reader'}, {'password2': 'mismatch'}, {'email': 'invalid'},
            {'age': 0}, {'age': -1}, {'weekly_reading_hours': 0}, {'annual_reading_count': -3},
            {'annual_reading_count': '1.5'}, {'interested_genres': ['UNKNOWN']}, {'gender': 'INVALID'},
            {'password1': '123', 'password2': '123'},
        ]:
            with self.subTest(changes=changes):
                response = self.client.post(reverse('accounts:signup'), self.signup_data(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_login_failure_then_success_changes_navigation(self):
        response = self.client.post(reverse('accounts:login'), {'username': self.user.username, 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        response = self.client.post(reverse('accounts:login'), {'username': self.user.username, 'password': self.password}, follow=True)
        self.assertContains(response, '내 프로필')
        self.assertContains(response, reverse('books:create'))
        self.assertNotContains(response, reverse('accounts:signup'))

    def test_safe_next_redirect(self):
        url = reverse('accounts:update')
        response = self.client.post(reverse('accounts:login'), {
            'username': self.user.username, 'password': self.password, 'next': url,
        })
        self.assertRedirects(response, url)

    def test_external_next_redirect_is_rejected(self):
        for next_url in ['https://evil.example/steal', '//evil.example', 'javascript:alert(1)']:
            self.client.logout()
            response = self.client.post(reverse('accounts:login'), {
                'username': self.user.username, 'password': self.password, 'next': next_url,
            })
            self.assertRedirects(response, reverse('books:index'))

    def test_authenticated_users_skip_login_and_signup(self):
        self.client.force_login(self.user)
        for name in ['login', 'signup']:
            self.assertRedirects(self.client.get(reverse(f'accounts:{name}')), reverse('books:index'))

    def test_profile_update_initial_genres_and_permission_protection(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:update'))
        self.assertEqual(response.context['form'].initial['interested_genres'], ['NOVEL', 'SCIENCE'])
        for forbidden in ['is_staff', 'is_superuser', 'user_permissions', 'groups', 'password']:
            self.assertNotIn(forbidden, response.context['form'].fields)
        response = self.client.post(reverse('accounts:update'), {
            'email': 'updated@example.com', 'last_name': '이', 'first_name': '책',
            'gender': 'F', 'age': 30, 'weekly_reading_hours': 7, 'annual_reading_count': 20,
            'interested_genres': ['SCIENCE', 'HISTORY'], 'is_staff': 'on', 'is_superuser': 'on',
        })
        self.assertRedirects(response, reverse('books:index'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.interested_genres, 'SCIENCE,HISTORY')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        response = self.client.get(reverse('accounts:profile', args=[self.user.username]))
        for value in ['이책', 'updated@example.com', '과학, 역사', '30세']:
            self.assertContains(response, value)

    def test_update_can_clear_genres(self):
        self.client.force_login(self.user)
        self.client.post(reverse('accounts:update'), {'email': self.user.email})
        self.user.refresh_from_db()
        self.assertEqual(self.user.interested_genres, '')

    def test_password_change_preserves_login_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:change_password'), {
            'old_password': self.password, 'new_password1': 'Another!Chapter2026',
            'new_password2': 'Another!Chapter2026',
        })
        self.assertRedirects(response, reverse('books:index'))
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Another!Chapter2026'))
        self.assertEqual(self.client.get(reverse('accounts:update')).status_code, 200)

    def test_wrong_current_password_does_not_change_password(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:change_password'), {
            'old_password': 'wrong', 'new_password1': 'Another!Chapter2026', 'new_password2': 'Another!Chapter2026',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))

    def test_logout_and_delete_are_post_only(self):
        self.client.force_login(self.user)
        for name in ['logout', 'delete']:
            self.assertEqual(self.client.get(reverse(f'accounts:{name}')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('accounts:logout')), reverse('books:index'))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.client.force_login(self.user)
        self.assertRedirects(self.client.post(reverse('accounts:delete')), reverse('books:index'))
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_account_pages_require_login(self):
        for name, args in [('update', []), ('change_password', []), ('profile', [self.user.username])]:
            url = reverse(f'accounts:{name}', args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse('accounts:login')))
        self.assertEqual(self.client.post(reverse('accounts:delete')).status_code, 302)

    def test_account_method_restrictions(self):
        for name in ['login', 'signup', 'update', 'change_password']:
            self.assertEqual(self.client.put(reverse(f'accounts:{name}')).status_code, 405)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('accounts:profile', args=[self.user.username])).status_code, 405)
        self.assertEqual(self.client.get(reverse('accounts:profile', args=['missing'])).status_code, 404)

    def test_csrf_protects_accounts(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('accounts:signup'), self.signup_data()).status_code, 403)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('accounts:delete')).status_code, 403)

    def test_forms_use_custom_user(self):
        self.assertIs(CustomUserCreationForm.Meta.model, User)
        self.assertIs(CustomUserChangeForm.Meta.model, User)
