from rest_framework import serializers
from apps.social.models import (
    Friendship, Circle, CircleMembership, CircleInvitation,
    CirclePost, CircleComment, FeedItem, Notification,
    Conversation, Message
)
from apps.users.serializers import UserSerializer
from apps.books.serializers import BookListSerializer
from apps.reading.serializers import QuoteListSerializer


# ===== FRIENDSHIP =====

class FriendshipSerializer(serializers.ModelSerializer):
    """Serializer for Friendship model"""
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = Friendship
        fields = [
            'id',
            'from_user',
            'to_user',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'from_user', 'created_at', 'updated_at']


class FriendshipCreateSerializer(serializers.ModelSerializer):
    """Serializer for sending friend requests"""
    
    class Meta:
        model = Friendship
        fields = ['to_user']
    
    def validate_to_user(self, value):
        """Validate friend request"""
        request = self.context.get('request')

        # Can't send request to yourself
        if value == request.user:
            raise serializers.ValidationError("Cannot send friend request to yourself")

        # Note: We don't check for existing friendships here anymore
        # The view's create() method handles that gracefully by returning the existing friendship

        return value


# ===== CIRCLES =====

class CircleMembershipSerializer(serializers.ModelSerializer):
    """Serializer for CircleMembership"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CircleMembership
        fields = [
            'id',
            'user',
            'role',
            'joined_at',
        ]
        read_only_fields = ['id', 'joined_at']


class CircleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for circle lists"""
    creator = UserSerializer(read_only=True)
    members_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Circle
        fields = [
            'id',
            'name',
            'description',
            'creator',
            'members_count',
            'max_members',
            'is_invite_only',
            'image',
            'created_at',
        ]
        read_only_fields = ['id', 'creator', 'created_at']


class CircleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single circle view"""
    creator = UserSerializer(read_only=True)
    memberships = CircleMembershipSerializer(many=True, read_only=True)
    members_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Circle
        fields = [
            'id',
            'name',
            'description',
            'creator',
            'memberships',
            'members_count',
            'max_members',
            'is_invite_only',
            'image',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']


class CircleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating circles"""
    
    class Meta:
        model = Circle
        fields = [
            'name',
            'description',
            'max_members',
            'is_invite_only',
            'image',
        ]
    
    def validate_max_members(self, value):
        """Validate max_members range"""
        if value < 2:
            raise serializers.ValidationError("Circle must allow at least 2 members")
        if value > 20:
            raise serializers.ValidationError("Circle cannot exceed 20 members")
        return value


class CircleInvitationSerializer(serializers.ModelSerializer):
    """Serializer for circle invitations"""
    circle = CircleListSerializer(read_only=True)
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = CircleInvitation
        fields = [
            'id',
            'circle',
            'from_user',
            'to_user',
            'status',
            'message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'from_user', 'created_at', 'updated_at']


class CircleInvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for sending circle invitations"""
    
    class Meta:
        model = CircleInvitation
        fields = [
            'circle',
            'to_user',
            'message',
        ]
    
    def validate(self, data):
        """Validate invitation"""
        circle = data.get('circle')
        to_user = data.get('to_user')
        request = self.context.get('request')
        
        # Check if user is admin of the circle
        membership = CircleMembership.objects.filter(
            circle=circle,
            user=request.user,
            role='admin'
        ).first()
        
        if not membership:
            raise serializers.ValidationError("Only circle admins can send invitations")
        
        # Check if circle is full
        if circle.members_count >= circle.max_members:
            raise serializers.ValidationError("Circle is full")
        
        # Check if user is already a member
        if CircleMembership.objects.filter(circle=circle, user=to_user).exists():
            raise serializers.ValidationError("User is already a member")
        
        # Check if invitation already exists
        if CircleInvitation.objects.filter(
            circle=circle,
            to_user=to_user,
            status='pending'
        ).exists():
            raise serializers.ValidationError("Invitation already sent")
        
        return data


# ===== CIRCLE POSTS =====

class CircleCommentSerializer(serializers.ModelSerializer):
    """Serializer for circle comments"""
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = CircleComment
        fields = [
            'id',
            'author',
            'content',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'author', 'post', 'created_at', 'updated_at']


class CirclePostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for circle post lists"""
    author = UserSerializer(read_only=True)
    circle_name = serializers.CharField(source='circle.name', read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CirclePost
        fields = [
            'id',
            'circle',
            'circle_name',
            'author',
            'post_type',
            'content',
            'comments_count',
            'created_at',
        ]
        read_only_fields = ['id', 'author', 'created_at']


class CirclePostDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single circle post view"""
    author = UserSerializer(read_only=True)
    circle = CircleListSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    quote = QuoteListSerializer(read_only=True)
    comments = CircleCommentSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CirclePost
        fields = [
            'id',
            'circle',
            'author',
            'post_type',
            'content',
            'book',
            'quote',
            'comments',
            'comments_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class CirclePostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating circle posts"""
    
    class Meta:
        model = CirclePost
        fields = [
            'circle',
            'post_type',
            'content',
            'book',
            'quote',
        ]
    
    def validate(self, data):
        """Validate post data"""
        post_type = data.get('post_type')
        book = data.get('book')
        quote = data.get('quote')
        
        # Validate required fields based on post_type
        if post_type == 'recommendation' and not book:
            raise serializers.ValidationError("Recommendations must include a book")
        
        if post_type == 'quote' and not quote:
            raise serializers.ValidationError("Quote posts must include a quote")
        
        # Validate user is member of circle
        circle = data.get('circle')
        request = self.context.get('request')
        
        if not CircleMembership.objects.filter(
            circle=circle,
            user=request.user
        ).exists():
            raise serializers.ValidationError("You must be a member of this circle to post")
        
        return data


# ===== NOTIFICATIONS =====

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    actor = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'actor',
            'notification_type',
            'message',
            'object_id',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['id', 'recipient', 'actor', 'created_at']


# ===== FEED =====

class FeedItemSerializer(serializers.ModelSerializer):
    """Serializer for feed items"""
    actor = UserSerializer(read_only=True)
    book_data = serializers.SerializerMethodField()
    review_data = serializers.SerializerMethodField()

    class Meta:
        model = FeedItem
        fields = [
            'id',
            'actor',
            'feed_type',
            'content_type',
            'object_id',
            'preview_text',
            'preview_image',
            'book_data',
            'review_data',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'actor', 'created_at']

    def get_review_data(self, obj):
        """Get review data for book_finished feed items"""
        if obj.content_type == 'UserBook' and obj.feed_type == 'book_finished':
            from apps.reading.models import UserBook
            try:
                user_book = UserBook.objects.get(id=obj.object_id)
                if user_book.review:
                    return user_book.review
            except UserBook.DoesNotExist:
                pass
        return None

    def get_book_data(self, obj):
        """Get structured book data for feed items"""
        if obj.content_type == 'UserBook':
            from apps.reading.models import UserBook
            try:
                user_book = UserBook.objects.select_related('book').get(id=obj.object_id)
                book = user_book.book
                authors = book.authors.all() if hasattr(book, 'authors') else []
                return {
                    'id': book.id,
                    'title': book.title,
                    'authors': [{'name': author.name} for author in authors],
                    'cover_image': book.cover_image if hasattr(book, 'cover_image') else None
                }
            except UserBook.DoesNotExist:
                return None
        elif obj.content_type == 'Quote':
            from apps.reading.models import Quote
            try:
                quote = Quote.objects.select_related('book').get(id=obj.object_id)
                book = quote.book
                if book:
                    authors = book.authors.all() if hasattr(book, 'authors') else []
                    return {
                        'id': book.id,
                        'title': book.title,
                        'authors': [{'name': author.name} for author in authors],
                        'cover_image': book.cover_image if hasattr(book, 'cover_image') else None
                    }
                # Fallback to quote's stored book info
                return {
                    'id': None,
                    'title': quote.book_title,
                    'authors': [{'name': quote.book_author}] if quote.book_author else [],
                    'cover_image': None
                }
            except Quote.DoesNotExist:
                return None
        return None


# ===== MESSAGES & CONVERSATIONS =====

class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages"""
    sender = UserSerializer(read_only=True)
    attached_book = BookListSerializer(read_only=True)
    attached_quote = QuoteListSerializer(read_only=True)
    is_own_message = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender',
            'content',
            'subject',
            'attached_book',
            'attached_quote',
            'is_important',
            'read_at',
            'is_own_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'sender', 'read_at', 'created_at', 'updated_at']

    def get_is_own_message(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.sender_id == request.user.id
        return False


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    recipient_id = serializers.IntegerField(write_only=True, required=False)
    attached_book_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    attached_quote_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Message
        fields = [
            'conversation',
            'recipient_id',
            'content',
            'subject',
            'attached_book_id',
            'attached_quote_id',
            'is_important',
        ]

    def validate(self, data):
        """Validate message data"""
        request = self.context.get('request')
        conversation = data.get('conversation')
        recipient_id = data.get('recipient_id')

        # Either conversation or recipient_id must be provided
        if not conversation and not recipient_id:
            raise serializers.ValidationError(
                "Either conversation or recipient_id must be provided"
            )

        # If recipient_id is provided, find or create conversation
        if recipient_id and not conversation:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                recipient = User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("Recipient not found")

            # Get or create conversation between users
            conversation = Conversation.get_or_create_between(request.user, recipient)
            data['conversation'] = conversation

        # Validate user is participant in conversation
        if conversation and not conversation.participants.filter(id=request.user.id).exists():
            raise serializers.ValidationError("You are not a participant in this conversation")

        # Handle book attachment
        if data.get('attached_book_id'):
            from apps.books.models import Book
            try:
                data['attached_book'] = Book.objects.get(id=data['attached_book_id'])
            except Book.DoesNotExist:
                raise serializers.ValidationError("Attached book not found")

        # Handle quote attachment
        if data.get('attached_quote_id'):
            from apps.reading.models import Quote
            try:
                data['attached_quote'] = Quote.objects.get(id=data['attached_quote_id'])
            except Quote.DoesNotExist:
                raise serializers.ValidationError("Attached quote not found")

        return data


class ConversationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for conversation lists"""
    other_participant = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'other_participant',
            'last_message_at',
            'last_message_preview',
            'last_message',
            'unread_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other = obj.get_other_participant(request.user)
            if other:
                return UserSerializer(other).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'id': last_msg.id,
                'content': last_msg.content[:100],
                'sender_id': last_msg.sender_id,
                'is_important': last_msg.is_important,
                'created_at': last_msg.created_at,
            }
        return None


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single conversation view"""
    participants = UserSerializer(many=True, read_only=True)
    other_participant = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'participants',
            'other_participant',
            'messages',
            'last_message_at',
            'unread_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'participants', 'created_at', 'updated_at']

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other = obj.get_other_participant(request.user)
            if other:
                return UserSerializer(other).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0


