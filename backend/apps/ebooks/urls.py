from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ebooks.views import EBookViewSet

router = DefaultRouter()
router.register(r'', EBookViewSet, basename='ebook')

urlpatterns = [
    path('', include(router.urls)),
]
