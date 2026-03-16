from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.books.models import Book, Author, Genre


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


# ---------------------------------------------------------------------------
# Book list
# ---------------------------------------------------------------------------
class TestBookList(TestCase):
    """Tests for GET /api/books/"""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)
        self.author = Author.objects.create(name='Fyodor Dostoevsky')
        self.genre = Genre.objects.create(name='Fiction', slug='fiction')

        self.book1 = Book.objects.create(
            title='Crime and Punishment', pages=671, language='en'
        )
        self.book1.authors.add(self.author)
        self.book1.genres.add(self.genre)

        self.book2 = Book.objects.create(
            title='The Brothers Karamazov', pages=824, language='en'
        )
        self.book2.authors.add(self.author)
        self.book2.genres.add(self.genre)

    def test_list_books(self):
        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)

    def test_list_books_unauthenticated(self):
        """Books list should be accessible without authentication."""
        anon_client = APIClient()
        response = anon_client.get('/api/books/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Book detail
# ---------------------------------------------------------------------------
class TestBookDetail(TestCase):
    """Tests for GET /api/books/{id}/"""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)
        self.author = Author.objects.create(name='Albert Camus')
        self.book = Book.objects.create(
            title='The Stranger', pages=123, language='en',
            description='A novel about an indifferent man.',
        )
        self.book.authors.add(self.author)

    def test_book_detail(self):
        response = self.client.get(f'/api/books/{self.book.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'The Stranger')

    def test_book_detail_not_found(self):
        response = self.client.get('/api/books/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Author list
# ---------------------------------------------------------------------------
class TestAuthorList(TestCase):
    """Tests for GET /api/books/authors/"""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)
        Author.objects.create(name='Hermann Hesse')
        Author.objects.create(name='Franz Kafka')

    def test_list_authors(self):
        response = self.client.get('/api/books/authors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)

    def test_list_authors_unauthenticated(self):
        anon_client = APIClient()
        response = anon_client.get('/api/books/authors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Author detail with books
# ---------------------------------------------------------------------------
class TestAuthorDetail(TestCase):
    """Tests for GET /api/books/authors/{id}/ and related books."""

    def setUp(self):
        self.user = _create_user()
        self.client = _make_client(self.user)
        self.author = Author.objects.create(name='Ernesto Sabato')
        self.book = Book.objects.create(
            title='The Tunnel', pages=152, language='es'
        )
        self.book.authors.add(self.author)

    def test_author_detail(self):
        response = self.client.get(f'/api/books/authors/{self.author.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Ernesto Sabato')

    def test_author_books(self):
        response = self.client.get(
            f'/api/books/authors/{self.author.id}/books/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'The Tunnel')

    def test_author_not_found(self):
        response = self.client.get('/api/books/authors/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
