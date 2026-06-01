from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reading.views import (
    UserBookViewSet,
    QuoteTagViewSet,
    QuoteViewSet,
    StudyNoteViewSet,
    VocabularyWordViewSet,
    ReadingSessionViewSet,
    unified_search,
)

app_name = 'reading'

router = DefaultRouter()
router.register(r'user-books', UserBookViewSet, basename='userbook')
router.register(r'quote-tags', QuoteTagViewSet, basename='quotetag')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'study-notes', StudyNoteViewSet, basename='studynote')
router.register(r'vocabulary', VocabularyWordViewSet, basename='vocabulary')
router.register(r'reading-sessions', ReadingSessionViewSet, basename='readingsession')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', unified_search, name='unified-search'),
]
