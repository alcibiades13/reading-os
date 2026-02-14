from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.social.views import (
    FriendshipViewSet,
    CircleViewSet,
    CircleInvitationViewSet,
    CirclePostViewSet,
    CircleCommentViewSet,
    FeedItemViewSet,
    NotificationViewSet,
    SuggestedUsersView,
    ConversationViewSet,
    MessageViewSet,
    DiscussionTopicViewSet,
    TopicMessageViewSet,
    BookClubReadingViewSet,
    ReviewCommentViewSet,
    ReviewLikeToggleView,
)

app_name = 'social'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'friendships', FriendshipViewSet, basename='friendship')
router.register(r'circles', CircleViewSet, basename='circle')
router.register(r'circle-invitations', CircleInvitationViewSet, basename='circleinvitation')
router.register(r'circle-posts', CirclePostViewSet, basename='circlepost')
router.register(r'circle-comments', CircleCommentViewSet, basename='circlecomment')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'feed', FeedItemViewSet, basename='feeditem')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
# Book Club / Discussion endpoints
router.register(r'topics', DiscussionTopicViewSet, basename='discussiontopic')
router.register(r'topic-messages', TopicMessageViewSet, basename='topicmessage')
router.register(r'club-readings', BookClubReadingViewSet, basename='bookclubreading')
router.register(r'review-comments', ReviewCommentViewSet, basename='reviewcomment')

urlpatterns = [
    path('', include(router.urls)),
    path('suggested-users/', SuggestedUsersView.as_view(), name='suggested-users'),
    path('review-likes/toggle/', ReviewLikeToggleView.as_view(), name='review-like-toggle'),
]

# This creates the following URLs:
# Friendships:
#   GET    /api/social/friendships/           - List friendships
#   POST   /api/social/friendships/           - Send friend request
#   GET    /api/social/friendships/{id}/      - Get friendship detail
#   DELETE /api/social/friendships/{id}/      - Remove friendship
#   POST   /api/social/friendships/{id}/accept/ - Accept request
#   POST   /api/social/friendships/{id}/decline/ - Decline request
#   GET    /api/social/friendships/pending/    - Get pending requests
#   GET    /api/social/friendships/my_friends/ - Get friends list
#
# Circles:
#   GET    /api/social/circles/               - List user's circles
#   POST   /api/social/circles/               - Create circle
#   GET    /api/social/circles/{id}/          - Get circle detail
#   PUT    /api/social/circles/{id}/          - Update circle
#   DELETE /api/social/circles/{id}/          - Delete circle
#   POST   /api/social/circles/{id}/leave/    - Leave circle
#   POST   /api/social/circles/{id}/promote_member/ - Promote to admin
#
# Circle Invitations:
#   GET    /api/social/circle-invitations/    - List invitations
#   POST   /api/social/circle-invitations/    - Send invitation
#   GET    /api/social/circle-invitations/{id}/ - Get invitation detail
#   POST   /api/social/circle-invitations/{id}/accept/ - Accept invitation
#   POST   /api/social/circle-invitations/{id}/decline/ - Decline invitation
#
# Circle Posts:
#   GET    /api/social/circle-posts/          - List posts from user's circles
#   GET    /api/social/circle-posts/?circle=X - Filter by circle
#   POST   /api/social/circle-posts/          - Create post
#   GET    /api/social/circle-posts/{id}/     - Get post detail
#   PUT    /api/social/circle-posts/{id}/     - Update post
#   DELETE /api/social/circle-posts/{id}/     - Delete post
#
# Circle Comments:
#   GET    /api/social/circle-comments/       - List comments
#   POST   /api/social/circle-comments/       - Create comment
#   GET    /api/social/circle-comments/{id}/  - Get comment detail
#   PUT    /api/social/circle-comments/{id}/  - Update comment
#   DELETE /api/social/circle-comments/{id}/  - Delete comment
#
# Feed:
#   GET    /api/social/feed/                  - Get user's feed
#   GET    /api/social/feed/{id}/             - Get feed item detail
#   POST   /api/social/feed/{id}/mark_read/   - Mark item as read
#   POST   /api/social/feed/mark_all_read/    - Mark all as read
#
# Conversations:
#   GET    /api/social/conversations/         - List user's conversations
#   POST   /api/social/conversations/         - Create conversation
#   GET    /api/social/conversations/{id}/    - Get conversation with messages
#   POST   /api/social/conversations/start/   - Start conversation with user
#   POST   /api/social/conversations/{id}/mark_read/ - Mark all messages as read
#
# Messages:
#   GET    /api/social/messages/              - List messages
#   GET    /api/social/messages/?conversation=X - Filter by conversation
#   POST   /api/social/messages/              - Send message
#   GET    /api/social/messages/{id}/         - Get message detail

