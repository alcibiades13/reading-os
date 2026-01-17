from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.challenges.views import ReadingChallengeViewSet

app_name = 'challenges'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', ReadingChallengeViewSet, basename='challenge')

urlpatterns = [
    path('', include(router.urls)),
]

# This creates the following URLs:
# Challenges:
#   GET    /api/challenges/                     - List user's challenges
#   GET    /api/challenges/?active=true         - Filter active challenges
#   GET    /api/challenges/?year=2025           - Filter by year
#   POST   /api/challenges/                     - Create challenge
#   GET    /api/challenges/{id}/                - Get challenge detail
#   PUT    /api/challenges/{id}/                - Update challenge
#   DELETE /api/challenges/{id}/                - Delete challenge
#   POST   /api/challenges/{id}/update_progress/ - Recalculate progress
#   POST   /api/challenges/{id}/toggle_active/   - Toggle active status
#   GET    /api/challenges/current/              - Get current challenges
#   GET    /api/challenges/completed/            - Get completed challenges
#   GET    /api/challenges/{id}/progress_details/ - Get progress breakdown

