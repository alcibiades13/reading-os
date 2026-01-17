from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.books.views import (
    AuthorViewSet,
    PublisherViewSet,
    GenreViewSet,
    TagViewSet,
    BookViewSet,
)

app_name = 'books'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(r'genres', GenreViewSet, basename='genre')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'', BookViewSet, basename='book')

urlpatterns = [
    path('', include(router.urls)),
]

# This creates the following URLs:
# Authors:
#   GET    /api/books/authors/           - List authors
#   POST   /api/books/authors/           - Create author
#   GET    /api/books/authors/{id}/      - Get author detail
#   GET    /api/books/authors/{id}/books/ - Get author's books
#
# Publishers:
#   GET    /api/books/publishers/        - List publishers
#   POST   /api/books/publishers/        - Create publisher
#   GET    /api/books/publishers/{id}/   - Get publisher detail
#
# Genres:
#   GET    /api/books/genres/            - List genres
#   GET    /api/books/genres/?parent=X   - Get subgenres
#   POST   /api/books/genres/            - Create genre
#   GET    /api/books/genres/{id}/       - Get genre detail
#
# Tags:
#   GET    /api/books/tags/              - List tags
#   GET    /api/books/tags/?category=X   - Filter by category
#   POST   /api/books/tags/              - Create tag
#
# Books:
#   GET    /api/books/                   - List books
#   GET    /api/books/?author=X          - Filter by author
#   GET    /api/books/?genre=X           - Filter by genre
#   GET    /api/books/?language=X        - Filter by language
#   POST   /api/books/                   - Create book
#   GET    /api/books/{id}/              - Get book detail
#   GET    /api/books/{id}/readers/      - Get book readers
#   GET    /api/books/{id}/quotes/       - Get public quotes
#   GET    /api/books/popular/           - Get popular books
#   GET    /api/books/recent/            - Get recent books

