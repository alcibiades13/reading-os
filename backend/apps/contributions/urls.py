from django.urls import path

from apps.contributions.views import (
    MyReputationView,
    MyBadgesView,
    MyContributionsView,
    UserReputationPublicView,
    ContributionLeaderboardView,
    ContributionDashboardView,
    ContributionReviewQueueView,
    ApproveContributionView,
    RejectContributionView,
    RevertContributionView,
    AwardBadgeView,
    AllBadgesView,
)

urlpatterns = [
    # Public (authenticated)
    path('my-reputation/', MyReputationView.as_view(), name='my-reputation'),
    path('my-badges/', MyBadgesView.as_view(), name='my-badges'),
    path('my-contributions/', MyContributionsView.as_view(), name='my-contributions'),
    path('user/<int:user_id>/reputation/', UserReputationPublicView.as_view(), name='user-reputation'),
    path('leaderboard/', ContributionLeaderboardView.as_view(), name='leaderboard'),
    path('badges/', AllBadgesView.as_view(), name='all-badges'),

    # Admin / Moderator
    path('dashboard/', ContributionDashboardView.as_view(), name='contribution-dashboard'),
    path('review-queue/', ContributionReviewQueueView.as_view(), name='review-queue'),
    path('<int:contribution_id>/approve/', ApproveContributionView.as_view(), name='approve-contribution'),
    path('<int:contribution_id>/reject/', RejectContributionView.as_view(), name='reject-contribution'),
    path('<int:contribution_id>/revert/', RevertContributionView.as_view(), name='revert-contribution'),
    path('award-badge/', AwardBadgeView.as_view(), name='award-badge'),
]
