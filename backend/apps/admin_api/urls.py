from django.urls import path

from apps.admin_api.views import (
    AdminStatsView,
    AdminDataIssuesView,
    AdminAuthorMergeCandidatesView,
    AdminBooksView,
    AdminDismissAuthorPairView,
    AdminUnlinkAuthorView,
    AdminBookMergeCandidatesView,
    AdminDismissBookPairView,
    AdminUnlinkBookView,
    AdminDeleteBookView,
)

urlpatterns = [
    path('stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('data-issues/', AdminDataIssuesView.as_view(), name='admin-data-issues'),
    path('author-merge-candidates/', AdminAuthorMergeCandidatesView.as_view(), name='admin-author-merge-candidates'),
    path('books/', AdminBooksView.as_view(), name='admin-books'),
    path('dismiss-author-pair/', AdminDismissAuthorPairView.as_view(), name='admin-dismiss-author-pair'),
    path('unlink-author/<int:author_id>/', AdminUnlinkAuthorView.as_view(), name='admin-unlink-author'),
    path('book-merge-candidates/', AdminBookMergeCandidatesView.as_view(), name='admin-book-merge-candidates'),
    path('dismiss-book-pair/', AdminDismissBookPairView.as_view(), name='admin-dismiss-book-pair'),
    path('unlink-book/<int:book_id>/', AdminUnlinkBookView.as_view(), name='admin-unlink-book'),
    path('delete-book/<int:book_id>/', AdminDeleteBookView.as_view(), name='admin-delete-book'),
]
