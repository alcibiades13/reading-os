from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # App API endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/books/', include('apps.books.urls')),
    path('api/reading/', include('apps.reading.urls')),
    path('api/lists/', include('apps.lists.urls')),
    path('api/challenges/', include('apps.challenges.urls')),
    path('api/social/', include('apps.social.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "Reading OS Admin"
admin.site.site_title = "Reading OS"
admin.site.index_title = "Welcome to Reading OS Administration"