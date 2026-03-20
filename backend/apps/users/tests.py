from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User, UserProfile, AccountToken


def _make_client(user):
    """Return an APIClient authenticated via JWT for the given user."""
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


def _create_user(email='test@example.com', password='TestPass123!', **kwargs):
    defaults = {'first_name': 'Test', 'last_name': 'User'}
    defaults.update(kwargs)
    return User.objects.create_user(email=email, password=password, **defaults)


class NoThrottleMixin:
    """Mixin that disables AuthRateThrottle for the entire test class."""

    def setUp(self):
        super().setUp()
        patcher = patch(
            'apps.users.views.AuthRateThrottle.allow_request',
            return_value=True,
        )
        patcher.start()
        self.addCleanup(patcher.stop)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestUserRegistration(NoThrottleMixin, TestCase):
    """Tests for POST /api/users/ (registration)"""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = '/api/users/'
        self.valid_data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }

    def test_registration_success(self):
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_registration_duplicate_email(self):
        _create_user(email='newuser@example.com')
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_mismatched_passwords(self):
        data = self.valid_data.copy()
        data['password_confirm'] = 'DifferentPass456!'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_missing_email(self):
        data = self.valid_data.copy()
        del data['email']
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_creates_profile(self):
        """User creation should auto-create a UserProfile via signal."""
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class TestUserLogin(NoThrottleMixin, TestCase):
    """Tests for POST /api/users/login/"""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = '/api/users/login/'
        self.user = _create_user()

    def test_login_success(self):
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'password': 'TestPass123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)

    def test_login_wrong_password(self):
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'password': 'WrongPassword!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_missing_fields(self):
        response = self.client.post(self.url, {
            'email': 'test@example.com',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_email(self):
        response = self.client.post(self.url, {
            'email': 'noone@example.com',
            'password': 'TestPass123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Current user (/me)
# ---------------------------------------------------------------------------
class TestCurrentUser(TestCase):
    """Tests for GET /api/users/me/"""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)

    def test_get_current_user(self):
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')

    def test_get_current_user_unauthenticated(self):
        client = APIClient()
        response = client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------
class TestChangePassword(TestCase):
    """Tests for POST /api/users/change-password/"""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)

    def test_change_password_success(self):
        response = self.client.post('/api/users/change-password/', {
            'current_password': 'TestPass123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePass456!'))

    def test_change_password_wrong_current(self):
        response = self.client.post('/api/users/change-password/', {
            'current_password': 'WrongPassword!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_change_password_mismatched_new(self):
        response = self.client.post('/api/users/change-password/', {
            'current_password': 'TestPass123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'DifferentPass789!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_missing_fields(self):
        response = self.client.post('/api/users/change-password/', {
            'current_password': 'TestPass123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Password reset flow
# ---------------------------------------------------------------------------
class TestPasswordReset(NoThrottleMixin, TestCase):
    """Tests for forgot-password and reset-password flow."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = _create_user()

    def test_forgot_password_existing_email(self):
        response = self.client.post('/api/users/forgot-password/', {
            'email': 'test@example.com',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AccountToken.objects.filter(
                user=self.user, token_type='password_reset', used=False
            ).exists()
        )

    def test_forgot_password_nonexistent_email(self):
        """Should return 200 even for nonexistent email (prevent enumeration)."""
        response = self.client.post('/api/users/forgot-password/', {
            'email': 'nonexistent@example.com',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_password_with_valid_token(self):
        token = AccountToken.objects.create(
            user=self.user, token_type='password_reset'
        )
        response = self.client.post('/api/users/reset-password/', {
            'token': str(token.token),
            'password': 'BrandNewPass789!',
            'password_confirm': 'BrandNewPass789!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('BrandNewPass789!'))
        token.refresh_from_db()
        self.assertTrue(token.used)

    def test_reset_password_invalid_token(self):
        response = self.client.post('/api/users/reset-password/', {
            'token': '00000000-0000-0000-0000-000000000000',
            'password': 'BrandNewPass789!',
            'password_confirm': 'BrandNewPass789!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_mismatched(self):
        token = AccountToken.objects.create(
            user=self.user, token_type='password_reset'
        )
        response = self.client.post('/api/users/reset-password/', {
            'token': str(token.token),
            'password': 'BrandNewPass789!',
            'password_confirm': 'DifferentPass!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------
class TestEmailVerification(TestCase):
    """Tests for send-verification and verify-email flow."""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)

    def test_send_verification_email(self):
        response = self.client.post('/api/users/send-verification/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AccountToken.objects.filter(
                user=self.user, token_type='email_verify', used=False
            ).exists()
        )

    def test_send_verification_already_verified(self):
        self.user.email_verified = True
        self.user.save(update_fields=['email_verified'])
        response = self.client.post('/api/users/send-verification/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('already verified', response.data['message'])

    def test_verify_email_with_valid_token(self):
        token = AccountToken.objects.create(
            user=self.user, token_type='email_verify'
        )
        anon_client = APIClient()
        response = anon_client.post('/api/users/verify-email/', {
            'token': str(token.token),
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        token.refresh_from_db()
        self.assertTrue(token.used)

    def test_verify_email_invalid_token(self):
        anon_client = APIClient()
        response = anon_client.post('/api/users/verify-email/', {
            'token': '00000000-0000-0000-0000-000000000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Account deletion
# ---------------------------------------------------------------------------
class TestAccountDeletion(TestCase):
    """Tests for POST /api/users/delete-account/"""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)

    def test_delete_account_success(self):
        response = self.client.post('/api/users/delete-account/', {
            'password': 'TestPass123!',
            'confirm': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(email='test@example.com').exists())

    def test_delete_account_wrong_password(self):
        response = self.client.post('/api/users/delete-account/', {
            'password': 'WrongPassword!',
            'confirm': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_delete_account_no_confirm(self):
        response = self.client.post('/api/users/delete-account/', {
            'password': 'TestPass123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_delete_account_unauthenticated(self):
        anon_client = APIClient()
        response = anon_client.post('/api/users/delete-account/', {
            'password': 'TestPass123!',
            'confirm': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
