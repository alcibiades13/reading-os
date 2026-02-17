from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.social.models import (
    Friendship, Circle, CircleMembership, CircleInvitation,
    CirclePost, CircleComment, FeedItem, FeedItemLike, FeedItemComment,
    Notification, Conversation, Message, DiscussionTopic, TopicMessage,
    TopicMessageLike, BookClubReading, ReviewLike, ReviewComment,
    MessageReaction, TopicReadStatus, Poll, PollOption, PollVote,
    CircleEvent,
)
from apps.social.serializers import (
    FriendshipSerializer, FriendshipCreateSerializer,
    CircleListSerializer, CircleDetailSerializer, CircleCreateSerializer,
    CircleMembershipSerializer, CircleInvitationSerializer,
    CircleInvitationCreateSerializer, CirclePostListSerializer,
    CirclePostDetailSerializer, CirclePostCreateSerializer,
    CircleCommentSerializer, FeedItemSerializer, FeedItemCommentSerializer,
    NotificationSerializer,
    ConversationListSerializer, ConversationDetailSerializer,
    MessageSerializer, MessageCreateSerializer,
    DiscussionTopicListSerializer, DiscussionTopicDetailSerializer,
    DiscussionTopicCreateSerializer, TopicMessageSerializer,
    TopicMessageCreateSerializer, BookClubReadingSerializer,
    BookClubReadingCreateSerializer,
    ReviewCommentSerializer, ReviewCommentCreateSerializer,
    CircleEventSerializer, CircleDiscoverySerializer,
)


# ===== FRIENDSHIP =====

class FriendshipViewSet(viewsets.ModelViewSet):
    """ViewSet for Friendship model"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return FriendshipCreateSerializer
        return FriendshipSerializer

    def get_queryset(self):
        """Get friendships for current user"""
        user = self.request.user
        return Friendship.objects.filter(
            from_user=user
        ) | Friendship.objects.filter(
            to_user=user
        )

    def create(self, request, *args, **kwargs):
        """Override create to handle existing friendships"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the to_user from validated data
        to_user = serializer.validated_data['to_user']

        # Check if friendship already exists
        existing_friendship = Friendship.objects.filter(
            from_user=request.user,
            to_user=to_user
        ).first()

        if existing_friendship:
            # Return existing friendship
            response_serializer = FriendshipSerializer(existing_friendship)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        # Create new friendship
        self.perform_create(serializer)

        # Get the created friendship to return it
        new_friendship = Friendship.objects.filter(
            from_user=request.user,
            to_user=to_user
        ).first()

        response_serializer = FriendshipSerializer(new_friendship)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Create friend request - auto-accept for follow functionality"""
        # Create the friendship
        friendship = serializer.save(from_user=self.request.user)

        # Explicitly set status to accepted (model default is 'pending')
        friendship.status = 'accepted'
        friendship.save()

        # Debug logging
        print(f"DEBUG Create Friendship - Created friendship ID: {friendship.id}")
        print(f"DEBUG Create Friendship - from_user: {friendship.from_user_id}, to_user: {friendship.to_user_id}, status: {friendship.status}")

        # Create notification for the followed user
        Notification.objects.create(
            recipient=friendship.to_user,
            actor=self.request.user,
            notification_type='new_follower',
            message=f'{self.request.user.first_name} {self.request.user.last_name} started following you',
            object_id=friendship.id
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept friend request"""
        friendship = self.get_object()
        
        if friendship.to_user != request.user:
            return Response(
                {'error': 'You can only accept requests sent to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        friendship.status = 'accepted'
        friendship.save()
        
        serializer = FriendshipSerializer(friendship)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline friend request"""
        friendship = self.get_object()
        
        if friendship.to_user != request.user:
            return Response(
                {'error': 'You can only decline requests sent to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        friendship.status = 'declined'
        friendship.save()
        
        serializer = FriendshipSerializer(friendship)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending friend requests"""
        friendships = Friendship.objects.filter(
            to_user=request.user,
            status='pending'
        )
        serializer = FriendshipSerializer(friendships, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_friends(self, request):
        """Get accepted friends"""
        friendships = Friendship.objects.filter(
            from_user=request.user,
            status='accepted'
        ) | Friendship.objects.filter(
            to_user=request.user,
            status='accepted'
        )
        serializer = FriendshipSerializer(friendships, many=True)
        return Response(serializer.data)


# ===== CIRCLES =====

class CircleViewSet(viewsets.ModelViewSet):
    """ViewSet for Circle model"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CircleCreateSerializer
        elif self.action == 'retrieve':
            return CircleDetailSerializer
        return CircleListSerializer
    
    def get_queryset(self):
        """Get circles user is member of"""
        return Circle.objects.filter(
            members=self.request.user
        ).prefetch_related('memberships__user')
    
    def perform_create(self, serializer):
        """Create circle and add creator as admin"""
        circle = serializer.save(creator=self.request.user)
        
        # Add creator as admin member
        CircleMembership.objects.create(
            circle=circle,
            user=self.request.user,
            role='admin'
        )
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave circle"""
        circle = self.get_object()
        
        try:
            membership = CircleMembership.objects.get(
                circle=circle,
                user=request.user
            )
            
            # Cannot leave if you're the only admin
            admin_count = CircleMembership.objects.filter(
                circle=circle,
                role='admin'
            ).count()
            
            if membership.role == 'admin' and admin_count == 1:
                return Response(
                    {'error': 'Cannot leave - you are the only admin. Promote another member first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            membership.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except CircleMembership.DoesNotExist:
            return Response(
                {'error': 'You are not a member of this circle'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def member_progress(self, request, pk=None):
        """Get all members' reading progress on the circle's current book"""
        circle = self.get_object()
        if not circle.current_book:
            return Response([])

        from apps.reading.models import UserBook
        memberships = circle.memberships.select_related('user').all()
        progress_data = []
        for membership in memberships:
            try:
                ub = UserBook.objects.get(user=membership.user, book=circle.current_book)
                progress_data.append({
                    'user': UserSerializer(membership.user).data,
                    'reading_progress': ub.reading_progress,
                    'current_page': ub.current_page,
                    'status': ub.status,
                })
            except UserBook.DoesNotExist:
                progress_data.append({
                    'user': UserSerializer(membership.user).data,
                    'reading_progress': 0,
                    'current_page': 0,
                    'status': 'not_started',
                })
        progress_data.sort(key=lambda x: x['reading_progress'], reverse=True)
        return Response(progress_data)

    @action(detail=True, methods=['get'])
    def unread_counts(self, request, pk=None):
        """Get unread message counts per topic for this circle"""
        circle = self.get_object()
        topics = circle.topics.all()
        counts = {}
        for topic in topics:
            read_status = TopicReadStatus.objects.filter(
                user=request.user, topic=topic
            ).first()
            if read_status:
                unread = topic.messages.filter(
                    created_at__gt=read_status.last_read_at
                ).exclude(author=request.user).count()
            else:
                unread = topic.messages.exclude(author=request.user).count()
            if unread > 0:
                counts[topic.id] = unread
        return Response(counts)

    @action(detail=False, methods=['get'])
    def discover(self, request):
        """List public circles the user hasn't joined"""
        user_circle_ids = CircleMembership.objects.filter(
            user=request.user
        ).values_list('circle_id', flat=True)
        public_circles = Circle.objects.filter(
            is_public=True
        ).exclude(id__in=user_circle_ids)
        serializer = CircleDiscoverySerializer(public_circles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a public circle"""
        circle = self.get_object()
        if not circle.is_public:
            return Response(
                {'error': 'This circle requires an invitation'},
                status=status.HTTP_403_FORBIDDEN
            )
        if circle.members.count() >= circle.max_members:
            return Response(
                {'error': 'This circle is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if CircleMembership.objects.filter(circle=circle, user=request.user).exists():
            return Response(
                {'error': 'You are already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        CircleMembership.objects.create(
            circle=circle, user=request.user, role='member'
        )
        return Response({'status': 'joined'})

    @action(detail=True, methods=['get', 'post'])
    def events(self, request, pk=None):
        """List or create events for a circle"""
        circle = self.get_object()
        if request.method == 'GET':
            events = CircleEvent.objects.filter(circle=circle)
            serializer = CircleEventSerializer(events, many=True)
            return Response(serializer.data)
        else:
            # Only admins can create events
            if not CircleMembership.objects.filter(
                circle=circle, user=request.user, role='admin'
            ).exists():
                return Response(
                    {'error': 'Only admins can create events'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = CircleEventSerializer(data={**request.data, 'circle': circle.id})
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def promote_member(self, request, pk=None):
        """Promote member to admin"""
        circle = self.get_object()
        user_id = request.data.get('user_id')
        
        # Check if requester is admin
        if not CircleMembership.objects.filter(
            circle=circle,
            user=request.user,
            role='admin'
        ).exists():
            return Response(
                {'error': 'Only admins can promote members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            membership = CircleMembership.objects.get(
                circle=circle,
                user_id=user_id
            )
            membership.role = 'admin'
            membership.save()
            
            serializer = CircleMembershipSerializer(membership)
            return Response(serializer.data)
            
        except CircleMembership.DoesNotExist:
            return Response(
                {'error': 'User is not a member of this circle'},
                status=status.HTTP_404_NOT_FOUND
            )


class CircleInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for CircleInvitation model"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CircleInvitationCreateSerializer
        return CircleInvitationSerializer
    
    def get_queryset(self):
        """Get invitations sent to current user"""
        return CircleInvitation.objects.filter(
            to_user=self.request.user
        ).select_related('circle', 'from_user', 'to_user')
    
    def perform_create(self, serializer):
        """Send invitation and create notification"""
        invitation = serializer.save(from_user=self.request.user, status='pending')

        # Create notification for invited user
        Notification.objects.create(
            recipient=invitation.to_user,
            actor=self.request.user,
            notification_type='circle_invitation',
            message=f'{self.request.user.first_name} {self.request.user.last_name} invited you to join {invitation.circle.name}',
            object_id=invitation.id
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept circle invitation"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Invitation already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user to circle
        CircleMembership.objects.create(
            circle=invitation.circle,
            user=request.user,
            role='member'
        )
        
        invitation.status = 'accepted'
        invitation.save()
        
        serializer = CircleInvitationSerializer(invitation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline circle invitation"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Invitation already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.status = 'declined'
        invitation.save()
        
        serializer = CircleInvitationSerializer(invitation)
        return Response(serializer.data)


# ===== CIRCLE POSTS =====

class CirclePostViewSet(viewsets.ModelViewSet):
    """ViewSet for CirclePost model"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CirclePostCreateSerializer
        elif self.action == 'retrieve':
            return CirclePostDetailSerializer
        return CirclePostListSerializer
    
    def get_queryset(self):
        """Get posts from circles user is member of"""
        user_circles = Circle.objects.filter(members=self.request.user)
        
        queryset = CirclePost.objects.filter(
            circle__in=user_circles
        ).select_related(
            'author',
            'circle',
            'book',
            'quote'
        ).prefetch_related('comments')
        
        # Filter by circle
        circle_id = self.request.query_params.get('circle', None)
        if circle_id:
            queryset = queryset.filter(circle_id=circle_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create post"""
        serializer.save(author=self.request.user)


class CircleCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for CircleComment model"""
    serializer_class = CircleCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get comments from circles user is member of"""
        user_circles = Circle.objects.filter(members=self.request.user)
        return CircleComment.objects.filter(
            post__circle__in=user_circles
        ).select_related('author', 'post')
    
    def perform_create(self, serializer):
        """Create comment"""
        serializer.save(author=self.request.user)


# ===== NOTIFICATIONS =====

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Notification model (read-only)"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get notifications for current user"""
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related('actor').order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({'status': 'All notifications marked as read'})


# ===== FEED =====

class FeedItemViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for FeedItem model (read-only)"""
    serializer_class = FeedItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get feed items for current user"""
        return FeedItem.objects.filter(
            user=self.request.user
        ).select_related('actor').order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark feed item as read"""
        feed_item = self.get_object()
        feed_item.is_read = True
        feed_item.save()
        serializer = FeedItemSerializer(feed_item)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all feed items as read"""
        FeedItem.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({'status': 'All items marked as read'})

    @action(detail=True, methods=['post'])
    def toggle_like(self, request, pk=None):
        """Toggle like on a feed item"""
        feed_item = self.get_object()
        like, created = FeedItemLike.objects.get_or_create(
            feed_item=feed_item,
            user=request.user
        )
        if not created:
            like.delete()
            feed_item.likes_count = max(0, feed_item.likes_count - 1)
            feed_item.save(update_fields=['likes_count'])
            return Response({'liked': False, 'likes_count': feed_item.likes_count})
        else:
            feed_item.likes_count += 1
            feed_item.save(update_fields=['likes_count'])
            return Response({'liked': True, 'likes_count': feed_item.likes_count})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """List comments for a feed item"""
        feed_item = self.get_object()
        comments = feed_item.comments.select_related('author').all()
        serializer = FeedItemCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to a feed item"""
        feed_item = self.get_object()
        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {'error': 'Content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        comment = FeedItemComment.objects.create(
            feed_item=feed_item,
            author=request.user,
            content=content
        )
        feed_item.comments_count += 1
        feed_item.save(update_fields=['comments_count'])
        serializer = FeedItemCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ===== USER DISCOVERY =====

from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from apps.users.serializers import UserSerializer
from django.db.models import Count, Q

User = get_user_model()


class SuggestedUsersView(APIView):
    """
    Get suggested users based on reading similarity.
    GET /api/social/suggested-users/?limit=10
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        current_user = request.user

        from apps.reading.models import UserBook
        from apps.books.models import Genre

        # Get current user's read books and genres
        current_user_books = list(UserBook.objects.filter(
            user=current_user,
            status='read'
        ).values_list('book_id', flat=True))

        current_user_genres = list(Genre.objects.filter(
            books__user_books__user=current_user,
            books__user_books__status='read'
        ).distinct().values_list('id', flat=True))

        # Get ALL users except current user and already followed
        existing_friendships = list(Friendship.objects.filter(
            from_user=current_user,
            status__in=['accepted', 'pending']
        ).values_list('to_user_id', flat=True))

        # Get ALL users except current user and already followed
        suggested_users = User.objects.exclude(
            id=current_user.id
        ).exclude(
            id__in=existing_friendships
        )

        # Calculate match score for each user
        users_with_scores = []
        for user in suggested_users[:limit * 2]:  # Get more to filter after scoring
            # Count shared books
            user_books = UserBook.objects.filter(
                user=user,
                status='read'
            ).values_list('book_id', flat=True)

            shared_books = set(current_user_books) & set(user_books)
            shared_books_count = len(shared_books)

            # Count shared genres
            user_genres = Genre.objects.filter(
                books__user_books__user=user,
                books__user_books__status='read'
            ).distinct().values_list('id', flat=True)

            shared_genres = set(current_user_genres) & set(user_genres)
            shared_genres_count = len(shared_genres)

            # Calculate match score (max 100)
            match_score = min(shared_books_count * 4, 40) + min(shared_genres_count * 10, 30)

            # Get friendship status
            is_following = Friendship.objects.filter(
                from_user=current_user,
                to_user=user,
                status='accepted'
            ).exists()

            is_follower = Friendship.objects.filter(
                from_user=user,
                to_user=current_user,
                status='accepted'
            ).exists()

            # Get top genres for this user
            top_genres = Genre.objects.filter(
                books__user_books__user=user,
                books__user_books__status='read'
            ).annotate(
                count=Count('books')
            ).order_by('-count').values_list('name', flat=True)[:3]

            # Serialize user
            user_data = UserSerializer(user, context={'request': request}).data
            user_data.update({
                'match_score': match_score,
                'shared_books_count': shared_books_count,
                'is_following': is_following,
                'is_follower': is_follower,
                'top_genres': list(top_genres),
                'books_read_count': UserBook.objects.filter(user=user, status='read').count(),
                'quotes_count': user.quotes.count(),
                'followers_count': Friendship.objects.filter(to_user=user, status='accepted').count(),
                'following_count': Friendship.objects.filter(from_user=user, status='accepted').count(),
            })

            users_with_scores.append(user_data)

        # Sort by match score
        users_with_scores.sort(key=lambda x: x['match_score'], reverse=True)

        # Return top N users
        return Response(users_with_scores[:limit])


# ===== MESSAGES & CONVERSATIONS =====

from django.utils import timezone


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for Conversation model"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationListSerializer

    def get_queryset(self):
        """Get conversations for current user"""
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants', 'messages').order_by('-last_message_at', '-created_at')

    def retrieve(self, request, *args, **kwargs):
        """Get conversation and mark messages as read"""
        instance = self.get_object()

        # Mark all unread messages from other participants as read
        Message.objects.filter(
            conversation=instance,
            read_at__isnull=True
        ).exclude(
            sender=request.user
        ).update(read_at=timezone.now())

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new conversation with a user"""
        recipient_id = request.data.get('recipient_id')

        if not recipient_id:
            return Response(
                {'error': 'recipient_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Recipient not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create conversation
        conversation = Conversation.get_or_create_between(request.user, recipient)

        serializer = ConversationDetailSerializer(conversation, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark all messages in conversation as read"""
        conversation = self.get_object()

        Message.objects.filter(
            conversation=conversation,
            read_at__isnull=True
        ).exclude(
            sender=request.user
        ).update(read_at=timezone.now())

        return Response({'status': 'Messages marked as read'})


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for Message model"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        """Get messages for conversations user is part of"""
        user_conversations = Conversation.objects.filter(participants=self.request.user)

        queryset = Message.objects.filter(
            conversation__in=user_conversations
        ).select_related('sender', 'attached_book', 'attached_quote')

        # Filter by conversation
        conversation_id = self.request.query_params.get('conversation', None)
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)

        return queryset.order_by('created_at')

    def perform_create(self, serializer):
        """Create message and send notification"""
        message = serializer.save(sender=self.request.user)

        # Create notification for recipient
        recipient = message.conversation.get_other_participant(self.request.user)
        if recipient:
            # Add 'new_message' to notification types if needed
            Notification.objects.create(
                recipient=recipient,
                actor=self.request.user,
                notification_type='new_follower',  # Reusing existing type; could add 'new_message'
                message=f'{self.request.user.first_name} {self.request.user.last_name} sent you a message',
                object_id=message.conversation_id
            )

    def create(self, request, *args, **kwargs):
        """Override create to return detailed message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Get the created message with full details
        message = Message.objects.select_related(
            'sender', 'attached_book', 'attached_quote'
        ).get(id=serializer.instance.id)

        response_serializer = MessageSerializer(message, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# ===== BOOK CLUBS / DISCUSSION TOPICS =====

class DiscussionTopicViewSet(viewsets.ModelViewSet):
    """ViewSet for DiscussionTopic model"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-is_pinned', '-updated_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return DiscussionTopicCreateSerializer
        elif self.action == 'retrieve':
            return DiscussionTopicDetailSerializer
        return DiscussionTopicListSerializer

    def get_queryset(self):
        """Get topics from circles user is member of"""
        user_circles = Circle.objects.filter(members=self.request.user)

        queryset = DiscussionTopic.objects.filter(
            circle__in=user_circles
        ).select_related('circle', 'creator', 'book')

        # Filter by circle
        circle_id = self.request.query_params.get('circle', None)
        if circle_id:
            queryset = queryset.filter(circle_id=circle_id)

        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def perform_create(self, serializer):
        """Create topic and notify circle members"""
        topic = serializer.save(creator=self.request.user)

        # If this is for the current book, link it
        if not topic.book and topic.circle.current_book:
            topic.book = topic.circle.current_book
            topic.save()

        # Notify circle members about new topic
        member_ids = topic.circle.members.exclude(
            id=self.request.user.id
        ).values_list('id', flat=True)
        notifications = [
            Notification(
                recipient_id=mid,
                actor=self.request.user,
                notification_type='new_topic',
                message=f'{self.request.user.first_name} started "{topic.title}" in {topic.circle.name}',
                object_id=topic.id
            )
            for mid in member_ids
        ]
        Notification.objects.bulk_create(notifications)

    @action(detail=True, methods=['post'])
    def toggle_pin(self, request, pk=None):
        """Toggle pin on a topic (admin only)"""
        topic = self.get_object()

        # Check if user is admin
        if not CircleMembership.objects.filter(
            circle=topic.circle,
            user=request.user,
            role='admin'
        ).exists():
            return Response(
                {'error': 'Only admins can pin topics'},
                status=status.HTTP_403_FORBIDDEN
            )

        topic.is_pinned = not topic.is_pinned
        topic.save(update_fields=['is_pinned'])
        return Response({'is_pinned': topic.is_pinned})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark topic as read for the current user"""
        topic = self.get_object()
        TopicReadStatus.objects.update_or_create(
            user=request.user,
            topic=topic,
            defaults={'last_read_at': timezone.now()}
        )
        return Response({'status': 'ok'})


class TopicMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for TopicMessage model"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return TopicMessageCreateSerializer
        return TopicMessageSerializer

    def get_queryset(self):
        """Get messages from topics in circles user is member of"""
        user_circles = Circle.objects.filter(members=self.request.user)

        queryset = TopicMessage.objects.filter(
            topic__circle__in=user_circles
        ).select_related('topic', 'author', 'attached_quote', 'attached_book')

        # Filter by topic
        topic_id = self.request.query_params.get('topic', None)
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        # Filter by timestamp (for polling)
        after = self.request.query_params.get('after', None)
        if after:
            from django.utils.dateparse import parse_datetime
            after_dt = parse_datetime(after)
            if after_dt:
                queryset = queryset.filter(created_at__gt=after_dt)

        return queryset

    def perform_create(self, serializer):
        """Create message and notify topic creator"""
        message = serializer.save(author=self.request.user)

        # Notify topic creator about the reply
        topic = message.topic
        if topic.creator_id != self.request.user.id:
            Notification.objects.create(
                recipient=topic.creator,
                actor=self.request.user,
                notification_type='topic_reply',
                message=f'{self.request.user.first_name} replied in "{topic.title}"',
                object_id=message.id
            )

    @action(detail=True, methods=['post'])
    def toggle_like(self, request, pk=None):
        """Toggle like on a message"""
        message = self.get_object()

        like, created = TopicMessageLike.objects.get_or_create(
            message=message,
            user=request.user
        )

        if not created:
            # Already liked, so unlike
            like.delete()
            message.likes_count = max(0, message.likes_count - 1)
            message.save(update_fields=['likes_count'])
            return Response({'liked': False, 'likes_count': message.likes_count})
        else:
            # New like
            message.likes_count += 1
            message.save(update_fields=['likes_count'])
            return Response({'liked': True, 'likes_count': message.likes_count})

    @action(detail=True, methods=['post'])
    def toggle_reaction(self, request, pk=None):
        """Toggle an emoji reaction on a message"""
        message = self.get_object()
        emoji = request.data.get('emoji')

        valid_emojis = [c[0] for c in MessageReaction.REACTION_CHOICES]
        if emoji not in valid_emojis:
            return Response(
                {'error': f'Invalid emoji. Choose from: {", ".join(valid_emojis)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reaction, created = MessageReaction.objects.get_or_create(
            message=message, user=request.user, emoji=emoji
        )
        if not created:
            reaction.delete()

        # Build reaction summary
        from django.db.models import Count
        reactions = MessageReaction.objects.filter(
            message=message
        ).values('emoji').annotate(count=Count('id'))
        summary = {r['emoji']: r['count'] for r in reactions}
        user_reactions = list(
            MessageReaction.objects.filter(
                message=message, user=request.user
            ).values_list('emoji', flat=True)
        )
        return Response({
            'reactions': summary,
            'user_reactions': user_reactions
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search messages within a circle"""
        query = request.query_params.get('q', '')
        circle_id = request.query_params.get('circle', None)
        if not query or not circle_id:
            return Response([])

        messages = TopicMessage.objects.filter(
            topic__circle_id=circle_id,
            topic__circle__members=request.user,
            content__icontains=query
        ).select_related('author', 'topic').order_by('-created_at')[:50]

        from apps.social.serializers import TopicMessageSerializer
        serializer = TopicMessageSerializer(
            messages, many=True, context={'request': request}
        )
        return Response(serializer.data)


class BookClubReadingViewSet(viewsets.ModelViewSet):
    """ViewSet for BookClubReading model"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return BookClubReadingCreateSerializer
        return BookClubReadingSerializer

    def get_queryset(self):
        """Get book readings from circles user is member of"""
        user_circles = Circle.objects.filter(members=self.request.user)

        queryset = BookClubReading.objects.filter(
            circle__in=user_circles
        ).select_related('circle', 'book')

        # Filter by circle
        circle_id = self.request.query_params.get('circle', None)
        if circle_id:
            queryset = queryset.filter(circle_id=circle_id)

        # Filter by status
        book_status = self.request.query_params.get('status', None)
        if book_status:
            queryset = queryset.filter(status=book_status)

        return queryset

    @action(detail=True, methods=['post'])
    def set_as_current(self, request, pk=None):
        """Set this book as the club's current reading"""
        reading = self.get_object()

        # Check if user is admin
        if not CircleMembership.objects.filter(
            circle=reading.circle,
            user=request.user,
            role='admin'
        ).exists():
            return Response(
                {'error': 'Only club admins can set current book'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update previous current to completed
        BookClubReading.objects.filter(
            circle=reading.circle,
            status='current'
        ).update(status='completed')

        # Set this as current
        reading.status = 'current'
        reading.save()

        # Update circle's current_book
        reading.circle.current_book = reading.book
        reading.circle.save(update_fields=['current_book'])

        # Notify circle members about new book
        member_ids = reading.circle.members.exclude(
            id=request.user.id
        ).values_list('id', flat=True)
        notifications = [
            Notification(
                recipient_id=mid,
                actor=request.user,
                notification_type='new_club_book',
                message=f'{request.user.first_name} set "{reading.book.title}" as the current book in {reading.circle.name}',
                object_id=reading.id
            )
            for mid in member_ids
        ]
        Notification.objects.bulk_create(notifications)

        serializer = BookClubReadingSerializer(reading)
        return Response(serializer.data)


# ===== REVIEW COMMENTS & LIKES =====

class ReviewCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for review comments.
    GET /api/social/review-comments/?user_book=<id>
    POST /api/social/review-comments/
    DELETE /api/social/review-comments/<id>/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCommentCreateSerializer
        return ReviewCommentSerializer

    def get_queryset(self):
        queryset = ReviewComment.objects.select_related('author').all()
        user_book_id = self.request.query_params.get('user_book')
        if user_book_id:
            queryset = queryset.filter(user_book_id=user_book_id)
        return queryset

    def create(self, request):
        serializer = ReviewCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.reading.models import UserBook
        user_book = UserBook.objects.get(id=serializer.validated_data['user_book_id'])

        comment = ReviewComment.objects.create(
            user_book=user_book,
            author=request.user,
            content=serializer.validated_data['content']
        )

        return Response(
            ReviewCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return Response(
                {'error': 'You can only delete your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewLikeToggleView(APIView):
    """
    POST /api/social/review-likes/toggle/
    Toggle like on a review. Body: { "user_book_id": <int> }
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Check like status for a review."""
        user_book_id = request.query_params.get('user_book_id')
        if not user_book_id:
            return Response(
                {'error': 'user_book_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        liked = ReviewLike.objects.filter(
            user_book_id=user_book_id, user=request.user
        ).exists()
        like_count = ReviewLike.objects.filter(user_book_id=user_book_id).count()

        return Response({
            'liked': liked,
            'like_count': like_count,
        })

    def post(self, request):
        user_book_id = request.data.get('user_book_id')
        if not user_book_id:
            return Response(
                {'error': 'user_book_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.reading.models import UserBook
        try:
            user_book = UserBook.objects.get(id=user_book_id)
        except UserBook.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        like, created = ReviewLike.objects.get_or_create(
            user_book=user_book,
            user=request.user
        )

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        like_count = ReviewLike.objects.filter(user_book=user_book).count()

        return Response({
            'liked': liked,
            'like_count': like_count,
        })


# ===== POLLS =====

from apps.social.serializers import (
    PollSerializer, PollCreateSerializer
)


class PollViewSet(viewsets.ModelViewSet):
    """ViewSet for Poll model"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return PollCreateSerializer
        return PollSerializer

    def get_queryset(self):
        user_circles = Circle.objects.filter(members=self.request.user)
        return Poll.objects.filter(
            topic__circle__in=user_circles
        ).select_related('topic__circle').prefetch_related('options__votes')

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """Toggle vote on a poll option"""
        poll = self.get_object()
        option_id = request.data.get('option_id')

        if poll.is_closed:
            return Response(
                {'error': 'This poll is closed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            option = poll.options.get(id=option_id)
        except PollOption.DoesNotExist:
            return Response(
                {'error': 'Invalid option'},
                status=status.HTTP_404_NOT_FOUND
            )

        vote, created = PollVote.objects.get_or_create(
            option=option, user=request.user
        )
        if not created:
            vote.delete()

        # If single-choice, remove votes from other options
        if not poll.allows_multiple and created:
            PollVote.objects.filter(
                option__poll=poll, user=request.user
            ).exclude(option=option).delete()

        serializer = PollSerializer(poll, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a poll (admin only)"""
        poll = self.get_object()

        if not CircleMembership.objects.filter(
            circle=poll.topic.circle,
            user=request.user,
            role='admin'
        ).exists():
            return Response(
                {'error': 'Only admins can close polls'},
                status=status.HTTP_403_FORBIDDEN
            )

        poll.closes_at = timezone.now()
        poll.save(update_fields=['closes_at'])
        serializer = PollSerializer(poll, context={'request': request})
        return Response(serializer.data)

