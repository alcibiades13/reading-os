from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.lists.views import ReadingListViewSet, ReadingListItemViewSet

app_name = 'lists'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'items', ReadingListItemViewSet, basename='listitem')
router.register(r'', ReadingListViewSet, basename='readinglist')

urlpatterns = [
    path('', include(router.urls)),
]

# This creates the following URLs:
# Reading Lists:
#   GET    /api/lists/                   - List user's reading lists
#   GET    /api/lists/?public=true       - Filter public lists
#   GET    /api/lists/?smart=true        - Filter smart lists
#   POST   /api/lists/                   - Create reading list
#   GET    /api/lists/{id}/              - Get list detail with books
#   PUT    /api/lists/{id}/              - Update list
#   DELETE /api/lists/{id}/              - Delete list
#   POST   /api/lists/{id}/add_book/     - Add book to list
#   DELETE /api/lists/{id}/remove_book/  - Remove book from list
#   POST   /api/lists/{id}/reorder/      - Reorder books in list
#
# List Items:
#   GET    /api/lists/items/             - List items (rarely used directly)
#   POST   /api/lists/items/             - Add item to list
#   GET    /api/lists/items/{id}/        - Get item detail
#   PUT    /api/lists/items/{id}/        - Update item
#   DELETE /api/lists/items/{id}/        - Delete item
