from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet

app_name = 'users'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]

# This creates the following URLs:
# GET    /api/users/              - List users
# POST   /api/users/              - Register new user
# GET    /api/users/{id}/         - Get user detail
# PUT    /api/users/{id}/         - Update user
# PATCH  /api/users/{id}/         - Partial update user
# DELETE /api/users/{id}/         - Delete user
# POST   /api/users/login/        - Login (custom action)
# GET    /api/users/me/           - Get current user (custom action)
# PUT    /api/users/update_profile/ - Update profile (custom action)
# GET    /api/users/{id}/stats/   - Get user stats (custom action)

