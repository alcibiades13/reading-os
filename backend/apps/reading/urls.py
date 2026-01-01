from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reading.views import (
    UserBookViewSet,
    QuoteTagViewSet,
    QuoteViewSet,
    StudyNoteViewSet,
)

app_name = 'reading'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'user-books', UserBookViewSet, basename='userbook')
router.register(r'quote-tags', QuoteTagViewSet, basename='quotetag')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'study-notes', StudyNoteViewSet, basename='studynote')

urlpatterns = [
    path('', include(router.urls)),
]

# This creates the following URLs:
# User Books:
#   GET    /api/reading/user-books/              - List user's books
#   GET    /api/reading/user-books/?status=X     - Filter by status
#   GET    /api/reading/user-books/?favorite=true - Filter favorites
#   POST   /api/reading/user-books/              - Add book to library
#   GET    /api/reading/user-books/{id}/         - Get user book detail
#   PUT    /api/reading/user-books/{id}/         - Update user book
#   DELETE /api/reading/user-books/{id}/         - Remove book from library
#   POST   /api/reading/user-books/{id}/update_progress/ - Update progress
#   POST   /api/reading/user-books/{id}/mark_finished/   - Mark as finished
#
# Quote Tags:
#   GET    /api/reading/quote-tags/              - List user's quote tags
#   POST   /api/reading/quote-tags/              - Create quote tag
#   GET    /api/reading/quote-tags/{id}/         - Get tag detail
#   PUT    /api/reading/quote-tags/{id}/         - Update tag
#   DELETE /api/reading/quote-tags/{id}/         - Delete tag
#
# Quotes:
#   GET    /api/reading/quotes/                  - List user's quotes
#   GET    /api/reading/quotes/?book=X           - Filter by book
#   GET    /api/reading/quotes/?tag=X            - Filter by tag
#   GET    /api/reading/quotes/?favorite=true    - Filter favorites
#   POST   /api/reading/quotes/                  - Create quote
#   GET    /api/reading/quotes/{id}/             - Get quote detail
#   PUT    /api/reading/quotes/{id}/             - Update quote
#   DELETE /api/reading/quotes/{id}/             - Delete quote
#   GET    /api/reading/quotes/my_favorites/     - Get favorite quotes
#   GET    /api/reading/quotes/by_tag/?tag_id=X  - Get quotes by tag
#   GET    /api/reading/quotes/search_semantic/?q=X - Semantic search
