from django.contrib import admin
from .models import (
    Friendship, Circle, CircleMembership, CircleInvitation, CirclePost,
    CircleComment, FeedItem, DiscussionTopic, TopicMessage, TopicMessageLike,
    BookClubReading, Notification, Conversation, Message
)


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['from_user__email', 'to_user__email']


class CircleMembershipInline(admin.TabularInline):
    """Inline display of circle members"""
    model = CircleMembership
    extra = 1
    fields = ['user', 'role', 'joined_at']
    readonly_fields = ['joined_at']


@admin.register(Circle)
class CircleAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'members_count', 'max_members', 'is_invite_only', 'current_book', 'created_at']
    list_filter = ['is_invite_only', 'created_at']
    search_fields = ['name', 'description', 'creator__email']
    inlines = [CircleMembershipInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'creator', 'image')
        }),
        ('Settings', {
            'fields': ('max_members', 'is_invite_only')
        }),
        ('Book Club', {
            'fields': ('accent_color', 'current_book'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CircleMembership)
class CircleMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'circle', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__email', 'circle__name']


@admin.register(CircleInvitation)
class CircleInvitationAdmin(admin.ModelAdmin):
    list_display = ['circle', 'from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['circle__name', 'from_user__email', 'to_user__email']


@admin.register(CirclePost)
class CirclePostAdmin(admin.ModelAdmin):
    list_display = ['circle', 'author', 'post_type', 'content_preview', 'comments_count', 'created_at']
    list_filter = ['post_type', 'created_at']
    search_fields = ['circle__name', 'author__email', 'content']
    
    fieldsets = (
        ('Circle & Author', {
            'fields': ('circle', 'author', 'post_type')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Attachments', {
            'fields': ('book', 'quote'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Show first 50 chars of content"""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(CircleComment)
class CircleCommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__email', 'content']
    
    def content_preview(self, obj):
        """Show first 50 chars of content"""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(FeedItem)
class FeedItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'actor', 'feed_type', 'is_read', 'created_at']
    list_filter = ['feed_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'actor__email', 'preview_text']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Users', {
            'fields': ('user', 'actor')
        }),
        ('Content', {
            'fields': ('feed_type', 'content_type', 'object_id')
        }),
        ('Preview Data', {
            'fields': ('preview_text', 'preview_image'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
    )


# Book Club Admin
@admin.register(DiscussionTopic)
class DiscussionTopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'circle', 'category', 'is_locked', 'is_pinned', 'message_count', 'created_at']
    list_filter = ['category', 'is_locked', 'is_pinned', 'created_at']
    search_fields = ['title', 'description', 'circle__name']

    fieldsets = (
        ('Basic Info', {
            'fields': ('circle', 'creator', 'title', 'description', 'category')
        }),
        ('Settings', {
            'fields': ('is_locked', 'required_progress', 'is_pinned', 'book')
        }),
    )


@admin.register(TopicMessage)
class TopicMessageAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'content_preview', 'likes_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__email', 'topic__title']

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(TopicMessageLike)
class TopicMessageLikeAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'created_at']
    list_filter = ['created_at']


@admin.register(BookClubReading)
class BookClubReadingAdmin(admin.ModelAdmin):
    list_display = ['circle', 'book', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['circle__name', 'book__title']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'actor', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__email', 'actor__email', 'message']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'last_message_at', 'last_message_preview']
    search_fields = ['participants__email']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'content_preview', 'is_important', 'created_at']
    list_filter = ['is_important', 'created_at']
    search_fields = ['sender__email', 'content', 'subject']

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


