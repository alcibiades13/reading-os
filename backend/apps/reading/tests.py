from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.books.models import Book, Author
from apps.reading.models import UserBook, Quote


def _create_user(email='test@example.com', password='TestPass123!', **kwargs):
    defaults = {'first_name': 'Test', 'last_name': 'User'}
    defaults.update(kwargs)
    return User.objects.create_user(email=email, password=password, **defaults)


def _make_client(user):
    """Return an APIClient authenticated via JWT for the given user."""
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


def _create_book(**kwargs):
    defaults = {'title': 'Test Book', 'pages': 300, 'language': 'en'}
    defaults.update(kwargs)
    return Book.objects.create(**defaults)


# ---------------------------------------------------------------------------
# UserBook CRUD
# ---------------------------------------------------------------------------
class TestUserBookCRUD(TestCase):
    """Tests for UserBook creation and basic operations."""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)
        self.author = Author.objects.create(name='Test Author')
        self.book = _create_book()
        self.book.authors.add(self.author)

    def test_create_userbook(self):
        """Add a book to the user's library."""
        response = self.client.post('/api/reading/user-books/', {
            'book': self.book.id,
            'status': 'want_to_read',
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(
            UserBook.objects.filter(user=self.user, book=self.book).exists()
        )

    def test_create_userbook_duplicate_returns_existing(self):
        """Adding the same book twice should return the existing entry."""
        self.client.post('/api/reading/user-books/', {
            'book': self.book.id, 'status': 'want_to_read',
        }, format='json')
        response = self.client.post('/api/reading/user-books/', {
            'book': self.book.id, 'status': 'want_to_read',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            UserBook.objects.filter(user=self.user, book=self.book).count(), 1
        )


# ---------------------------------------------------------------------------
# Reading progress
# ---------------------------------------------------------------------------
class TestReadingProgress(TestCase):
    """Tests for the update_progress action."""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)
        self.book = _create_book(pages=300)
        self.user_book = UserBook.objects.create(
            user=self.user, book=self.book, status='currently_reading',
        )
        self.url = f'/api/reading/user-books/{self.user_book.id}/update_progress/'

    def test_update_progress_success(self):
        response = self.client.post(self.url, {'current_page': 150}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_book.refresh_from_db()
        self.assertEqual(self.user_book.current_page, 150)

    def test_update_progress_exceeding_page_count(self):
        response = self.client.post(self.url, {'current_page': 999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_update_progress_non_integer(self):
        response = self.client.post(self.url, {'current_page': 'abc'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_progress_negative(self):
        response = self.client.post(self.url, {'current_page': -5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------
class TestStatusTransition(TestCase):
    """Test invalid status transitions are blocked."""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)
        self.book = _create_book()
        self.user_book = UserBook.objects.create(
            user=self.user, book=self.book, status='read',
        )

    def test_read_to_want_to_read_blocked(self):
        """Cannot transition from 'read' back to 'want_to_read'."""
        response = self.client.patch(
            f'/api/reading/user-books/{self.user_book.id}/',
            {'status': 'want_to_read'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_read_to_currently_reading_blocked(self):
        """Cannot transition from 'read' back to 'currently_reading'."""
        response = self.client.patch(
            f'/api/reading/user-books/{self.user_book.id}/',
            {'status': 'currently_reading'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# IDOR protection
# ---------------------------------------------------------------------------
class TestIDORProtection(TestCase):
    """IDOR: user A cannot see user B's private books via ?user= parameter."""

    def setUp(self):
        # User A (attacker)
        self.user_a = _create_user(email='usera@example.com', first_name='Alice')
        self.client_a = _make_client(self.user_a)

        # User B (victim) -- private profile
        self.user_b = _create_user(email='userb@example.com', first_name='Bob')
        self.user_b.profile.is_public = False
        self.user_b.profile.save()

        # Give user B a book
        self.book = _create_book(title='Secret Book')
        self.user_book_b = UserBook.objects.create(
            user=self.user_b, book=self.book, status='currently_reading',
        )

    def test_cannot_see_private_user_books(self):
        """User A should get empty results when querying private user B's books."""
        response = self.client_a.get(
            f'/api/reading/user-books/?user={self.user_b.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_can_see_public_user_books(self):
        """User A CAN see user B's books when B's profile is public."""
        self.user_b.profile.is_public = True
        self.user_b.profile.save()

        response = self.client_a.get(
            f'/api/reading/user-books/?user={self.user_b.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_cannot_see_private_user_quotes(self):
        """User A should get empty results when querying private user B's quotes."""
        Quote.objects.create(
            user=self.user_b, book=self.book, text='A secret quote', is_public=True,
        )
        response = self.client_a.get(
            f'/api/reading/quotes/?user={self.user_b.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


# ---------------------------------------------------------------------------
# Quote CRUD
# ---------------------------------------------------------------------------
class TestQuoteCRUD(TestCase):
    """Tests for Quote create, list, update, delete."""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)
        self.book = _create_book()
        self.user_book = UserBook.objects.create(
            user=self.user, book=self.book, status='currently_reading',
        )

    def test_create_quote(self):
        response = self.client.post('/api/reading/quotes/', {
            'book': self.book.id,
            'user_book': self.user_book.id,
            'text': 'To be or not to be.',
            'page_number': 42,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Quote.objects.filter(user=self.user, text='To be or not to be.').exists()
        )

    def test_list_quotes(self):
        Quote.objects.create(user=self.user, book=self.book, text='Quote 1')
        Quote.objects.create(user=self.user, book=self.book, text='Quote 2')
        response = self.client.get('/api/reading/quotes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_quote(self):
        quote = Quote.objects.create(
            user=self.user, book=self.book, text='Original text'
        )
        response = self.client.patch(
            f'/api/reading/quotes/{quote.id}/',
            {'text': 'Updated text'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        quote.refresh_from_db()
        self.assertEqual(quote.text, 'Updated text')

    def test_delete_quote(self):
        quote = Quote.objects.create(
            user=self.user, book=self.book, text='Deletable quote'
        )
        response = self.client.delete(f'/api/reading/quotes/{quote.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quote.objects.filter(id=quote.id).exists())


# ---------------------------------------------------------------------------
# Wishlist privacy
# ---------------------------------------------------------------------------
class TestWishlistPrivacy(TestCase):
    """Test that the wishlist endpoint respects profile privacy."""

    def setUp(self):
        self.user_a = _create_user(email='usera@example.com', first_name='Alice')
        self.client_a = _make_client(self.user_a)

        self.user_b = _create_user(email='userb@example.com', first_name='Bob')
        self.user_b.profile.is_public = False
        self.user_b.profile.save()

        self.book = _create_book(title='Wishlist Book')
        UserBook.objects.create(
            user=self.user_b, book=self.book,
            status='want_to_read', is_wishlisted=True,
        )

    def test_private_user_wishlist_blocked(self):
        response = self.client_a.get(
            f'/api/reading/user-books/wishlist/?user={self.user_b.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_user_wishlist_visible(self):
        self.user_b.profile.is_public = True
        self.user_b.profile.save()
        response = self.client_a.get(
            f'/api/reading/user-books/wishlist/?user={self.user_b.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
