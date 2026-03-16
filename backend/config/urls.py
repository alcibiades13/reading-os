from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.db import connection
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


def health_check(request):
    """Health check endpoint for load balancers and monitoring."""
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    healthy = db_ok
    return JsonResponse(
        {'status': 'ok' if healthy else 'unhealthy', 'database': db_ok},
        status=200 if healthy else 503,
    )


urlpatterns = [
    # Health check
    path('api/health/', health_check, name='health_check'),

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
    path('api/codex/', include('apps.codex.urls')),
    path('api/admin-console/', include('apps.admin_api.urls')),
    path('api/contributions/', include('apps.contributions.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "Reading OS Admin"
admin.site.site_title = "Reading OS"
admin.site.index_title = "Welcome to Reading OS Administration"