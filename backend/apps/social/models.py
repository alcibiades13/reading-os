from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator

from apps.books.models import Book
from apps.reading.models import Quote


class Friendship(models.Model):
    """
    Friend connections between users.
    Bidirectional relationship managed through status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('blocked', 'Blocked'),
    ]
    
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_friend_requests'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_friend_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
        verbose_name = 'Friendship'
        verbose_name_plural = 'Friendships'
    
    def __str__(self):
        return f"{self.from_user.email} -> {self.to_user.email} ({self.status})"


class Circle(models.Model):
    """
    Private reading circles (2-10 people).
    Intimate groups for sharing quotes, recommendations, discussions.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_circles'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='CircleMembership',
        related_name='circles'
    )
    
    # Settings
    max_members = models.IntegerField(
        default=10,
        validators=[MaxValueValidator(20)],
        help_text="Maximum number of members (default: 10)"
    )
    is_invite_only = models.BooleanField(
        default=True,
        help_text="Members can only join by invitation"
    )
    
    # Avatar/image
    image = models.ImageField(
        upload_to='circles/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Circle'
        verbose_name_plural = 'Circles'
    
    def __str__(self):
        return self.name
    
    @property
    def members_count(self):
        """Number of active members"""
        return self.members.count()


class CircleMembership(models.Model):
    """
    Through model for Circle membership with roles.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    circle = models.ForeignKey(
        Circle,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'circle']
        verbose_name = 'Circle Membership'
        verbose_name_plural = 'Circle Memberships'
    
    def __str__(self):
        return f"{self.user.email} in {self.circle.name} ({self.role})"


class CircleInvitation(models.Model):
    """
    Invitations to join circles.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    circle = models.ForeignKey(
        Circle,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_circle_invitations'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_circle_invitations'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['circle', 'to_user']
        verbose_name = 'Circle Invitation'
        verbose_name_plural = 'Circle Invitations'
    
    def __str__(self):
        return f"{self.circle.name} -> {self.to_user.email} ({self.status})"


class CirclePost(models.Model):
    """
    Posts in circles: quotes, recommendations, discussions.
    Central to circle interaction.
    """
    POST_TYPE_CHOICES = [
        ('quote', 'Quote Share'),
        ('recommendation', 'Book Recommendation'),
        ('discussion', 'Discussion'),
        ('update', 'Reading Update'),
    ]
    
    circle = models.ForeignKey(
        Circle,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='circle_posts'
    )
    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPE_CHOICES
    )
    
    # Content
    content = models.TextField(help_text="Post text/message")
    
    # Optional attachments
    book = models.ForeignKey(
        Book,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Referenced book"
    )
    quote = models.ForeignKey(
        Quote,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Shared quote"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Circle Post'
        verbose_name_plural = 'Circle Posts'
    
    def __str__(self):
        return f"{self.circle.name} - {self.author.email} ({self.post_type})"
    
    @property
    def comments_count(self):
        """Number of comments on this post"""
        return self.comments.count()


class CircleComment(models.Model):
    """
    Comments on circle posts.
    """
    post = models.ForeignKey(
        CirclePost,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='circle_comments'
    )
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Circle Comment'
        verbose_name_plural = 'Circle Comments'
    
    def __str__(self):
        return f"Comment by {self.author.email} on post {self.post.id}"


class Notification(models.Model):
    """
    User notifications for social interactions.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('new_follower', 'New Follower'),
        ('circle_invitation', 'Circle Invitation'),
        ('circle_post', 'New Circle Post'),
        ('comment', 'New Comment'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='triggered_notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES
    )

    # Optional reference to related object
    object_id = models.IntegerField(null=True, blank=True)

    # Preview text
    message = models.TextField()

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.email}"


class FeedItem(models.Model):
    """
    Aggregated activity feed for users.
    Shows updates from friends and circles.
    """
    FEED_TYPE_CHOICES = [
        ('book_finished', 'Book Finished'),
        ('book_started', 'Book Started'),
        ('want_to_read', 'Want to Read'),
        ('progress_update', 'Progress Update'),
        ('quote_added', 'Quote Added'),
        ('circle_post', 'Circle Post'),
        ('friend_joined', 'Friend Joined'),
        ('list_created', 'List Created'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feed_items',
        help_text="User who sees this in their feed"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performed_actions',
        help_text="User who performed the action"
    )
    
    feed_type = models.CharField(
        max_length=30,
        choices=FEED_TYPE_CHOICES
    )
    
    # Polymorphic content references
    content_type = models.CharField(
        max_length=50,
        help_text="Model name (Quote, CirclePost, UserBook, etc.)"
    )
    object_id = models.IntegerField(
        help_text="ID of the related object"
    )
    
    # Denormalized data for quick display
    preview_text = models.TextField(
        blank=True,
        help_text="Cached preview text"
    )
    preview_image = models.URLField(
        blank=True,
        help_text="Cached image URL"
    )
    
    is_read = models.BooleanField(
        default=False,
        help_text="Has user seen this feed item?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Feed Item'
        verbose_name_plural = 'Feed Items'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.actor.email} - {self.feed_type} (for {self.user.email})"


class Conversation(models.Model):
    """
    A conversation between two users.
    Supports 1:1 private messaging.
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )

    # Denormalized for quick access
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_preview = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at', '-created_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'

    def __str__(self):
        participant_emails = ', '.join([u.email for u in self.participants.all()[:2]])
        return f"Conversation: {participant_emails}"

    def get_other_participant(self, user):
        """Get the other participant in a 1:1 conversation"""
        return self.participants.exclude(id=user.id).first()

    def get_unread_count(self, user):
        """Get count of unread messages for a user in this conversation"""
        return self.messages.filter(read_at__isnull=True).exclude(sender=user).count()

    @classmethod
    def get_or_create_between(cls, user1, user2):
        """Get existing conversation between two users or create a new one"""
        # Find conversation where both users are participants
        conversation = cls.objects.filter(
            participants=user1
        ).filter(
            participants=user2
        ).first()

        if not conversation:
            conversation = cls.objects.create()
            conversation.participants.add(user1, user2)

        return conversation


class Message(models.Model):
    """
    A message in a conversation.
    Can have optional book or quote attachments.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    # Content
    content = models.TextField()
    subject = models.CharField(max_length=200, blank=True, help_text="Optional subject line")

    # Attachments
    attached_book = models.ForeignKey(
        Book,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='message_attachments',
        help_text="Attached book recommendation"
    )
    attached_quote = models.ForeignKey(
        Quote,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='message_attachments',
        help_text="Attached quote"
    )

    # Metadata
    is_important = models.BooleanField(default=False, help_text="Starred/important message")
    read_at = models.DateTimeField(null=True, blank=True, help_text="When recipient read the message")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender.email} at {self.created_at}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update conversation's last message info
        self.conversation.last_message_at = self.created_at
        self.conversation.last_message_preview = self.content[:100] if self.content else ''
        self.conversation.save(update_fields=['last_message_at', 'last_message_preview', 'updated_at'])


