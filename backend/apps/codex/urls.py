from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.codex.views import JournalEntryViewSet, ManuscriptViewSet, ChapterViewSet

router = DefaultRouter()
router.register(r'journal', JournalEntryViewSet, basename='journal')
router.register(r'manuscripts', ManuscriptViewSet, basename='manuscript')
router.register(r'chapters', ChapterViewSet, basename='chapter')

urlpatterns = [
    path('', include(router.urls)),
]
