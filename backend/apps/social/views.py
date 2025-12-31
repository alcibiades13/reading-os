from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.social.models import (
    Friendship, Circle, CircleMembership, CircleInvitation,
    CirclePost, CircleComment, FeedItem
)
from apps.social.serializers import (
    FriendshipSerializer, FriendshipCreateSerializer,
    CircleListSerializer, CircleDetailSerializer, CircleCreateSerializer,
    CircleMembershipSerializer, CircleInvitationSerializer,
    CircleInvitationCreateSerializer, CirclePostListSerializer,
    CirclePostDetailSerializer, CirclePostCreateSerializer,
    CircleCommentSerializer, FeedItemSerializer,
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
    
    def perform_create(self, serializer):
        """Create friend request"""
        serializer.save(from_user=self.request.user, status='pending')
    
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
        """Send invitation"""
        serializer.save(from_user=self.request.user, status='pending')
    
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
