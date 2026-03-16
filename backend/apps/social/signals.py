import threading

from django.db.models import F
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.reading.models import Quote, UserBook
from apps.social.models import (
    Conversation, FeedItem, Friendship, Message,
    TopicMessage, TopicMessageLike,
)

User = get_user_model()

# Thread-safe storage for UserBook pre-save state
_thread_local = threading.local()


def _get_pre_save_state():
    """Get the thread-local pre-save state dict, creating it if needed."""
    if not hasattr(_thread_local, 'userbook_pre_save_state'):
        _thread_local.userbook_pre_save_state = {}
    return _thread_local.userbook_pre_save_state


@receiver(pre_save, sender=UserBook)
def store_userbook_pre_save_state(sender, instance, **kwargs):
    """Store the previous state of UserBook before saving"""
    if instance.pk:
        try:
            old_instance = UserBook.objects.get(pk=instance.pk)
            _get_pre_save_state()[instance.pk] = {
                'status': old_instance.status,
                'current_page': old_instance.current_page,
            }
        except UserBook.DoesNotExist:
            pass


@receiver(post_save, sender=Quote)
def create_quote_feed_item(sender, instance, created, **kwargs):
    """Create feed item when user adds a quote"""
    if not created or not instance.is_public:
        return

    # Get all users who follow this user
    followers = Friendship.objects.filter(
        to_user=instance.user,
        status='accepted'
    ).values_list('from_user', flat=True)

    # Create feed item for each follower AND for the user themselves
    feed_items = []

    # Add feed item for the user themselves (for "My Updates")
    feed_items.append(FeedItem(
        user=instance.user,
        actor=instance.user,
        feed_type='quote_added',
        content_type='Quote',
        object_id=instance.id,
        preview_text=f'"{instance.text[:200]}..." - {instance.book_title}',
        preview_image='',
    ))

    # Add feed item for each follower
    for follower_id in followers:
        feed_items.append(FeedItem(
            user_id=follower_id,
            actor=instance.user,
            feed_type='quote_added',
            content_type='Quote',
            object_id=instance.id,
            preview_text=f'"{instance.text[:200]}..." - {instance.book_title}',
            preview_image='',
        ))

    if feed_items:
        FeedItem.objects.bulk_create(feed_items)


@receiver(post_save, sender=UserBook)
def create_userbook_feed_item(sender, instance, created, **kwargs):
    """Create feed item when user finishes a book, starts reading, or updates progress"""

    # Get all users who follow this user
    followers = Friendship.objects.filter(
        to_user=instance.user,
        status='accepted'
    ).values_list('from_user', flat=True)

    # Get previous state (thread-safe)
    pre_save_state = _get_pre_save_state()
    old_state = pre_save_state.pop(instance.pk, {})
    old_status = old_state.get('status')
    old_page = old_state.get('current_page')

    # Handle want_to_read status (only when status changes TO want_to_read or when created with want_to_read)
    status_changed_to_want = old_status and old_status != 'want_to_read' and instance.status == 'want_to_read'
    if (instance.status == 'want_to_read' and created) or status_changed_to_want:
        # Check if we already created a "want to read" feed item
        existing_want = FeedItem.objects.filter(
            actor=instance.user,
            content_type='UserBook',
            object_id=instance.id,
            feed_type='want_to_read'
        ).exists()

        if not existing_want:
            feed_items = []
            preview_text = f'wants to read {instance.book.title}'

            # Add feed item for the user themselves
            feed_items.append(FeedItem(
                user=instance.user,
                actor=instance.user,
                feed_type='want_to_read',
                content_type='UserBook',
                object_id=instance.id,
                preview_text=preview_text,
                preview_image=instance.book.cover_image if hasattr(instance.book, 'cover_image') and instance.book.cover_image else '',
            ))

            # Add feed item for each follower
            for follower_id in followers:
                feed_items.append(FeedItem(
                    user_id=follower_id,
                    actor=instance.user,
                    feed_type='want_to_read',
                    content_type='UserBook',
                    object_id=instance.id,
                    preview_text=preview_text,
                    preview_image=instance.book.cover_image if hasattr(instance.book, 'cover_image') and instance.book.cover_image else '',
                ))

            if feed_items:
                FeedItem.objects.bulk_create(feed_items)

    # Handle book started (status changes TO currently_reading)
    status_changed_to_reading = old_status and old_status != 'currently_reading' and instance.status == 'currently_reading'
    if (instance.status == 'currently_reading' and created) or status_changed_to_reading:
        # Check if we already created a "started" feed item
        existing_started = FeedItem.objects.filter(
            actor=instance.user,
            content_type='UserBook',
            object_id=instance.id,
            feed_type='book_started'
        ).exists()

        if not existing_started:
            feed_items = []
            preview_text = f'started reading {instance.book.title}'

            # Add feed item for the user themselves
            feed_items.append(FeedItem(
                user=instance.user,
                actor=instance.user,
                feed_type='book_started',
                content_type='UserBook',
                object_id=instance.id,
                preview_text=preview_text,
                preview_image=instance.book.cover_image if hasattr(instance.book, 'cover_image') and instance.book.cover_image else '',
            ))

            # Add feed item for each follower
            for follower_id in followers:
                feed_items.append(FeedItem(
                    user_id=follower_id,
                    actor=instance.user,
                    feed_type='book_started',
                    content_type='UserBook',
                    object_id=instance.id,
                    preview_text=preview_text,
                    preview_image=instance.book.cover_image if hasattr(instance.book, 'cover_image') and instance.book.cover_image else '',
                ))

            if feed_items:
                FeedItem.objects.bulk_create(feed_items)

    # Handle progress update (currently_reading with current_page changed)
    page_changed = old_page is not None and old_page != instance.current_page
    if instance.status == 'currently_reading' and instance.current_page and (not created) and page_changed:
        feed_items = []
        total_pages = instance.book.pages if hasattr(instance.book, 'pages') and instance.book.pages else 0

        if total_pages > 0:
            progress_percent = int((instance.current_page / total_pages) * 100)
            preview_text = f'made {progress_percent}% progress on {instance.book.title}'
        else:
            preview_text = f'is reading {instance.book.title} (page {instance.current_page})'

        # Add feed item for the user themselves
        feed_items.append(FeedItem(
            user=instance.user,
            actor=instance.user,
            feed_type='progress_update',
            content_type='UserBook',
            object_id=instance.id,
            preview_text=preview_text,
            preview_image=instance.book.cover_image if hasattr(instance.book, 'cover_image') and instance.book.cover_image else '',
        ))

        # Add feed item for each follower
        for follower_id in followers:
            feed_items.append(FeedItem(
                user_id=follower_id,
                actor=instance.user,
                feed_type='progress_update',
                content_type='UserBook',
                object_id=instance.id,
                preview_text=preview_text,
                preview_image=instance.book.cover_image if hasattr(instance.book, 'cover_image') and instance.book.cover_image else '',
            ))

        if feed_items:
            FeedItem.objects.bulk_create(feed_items)

    # Handle finished books
    if instance.status == 'read' and instance.finished_at:
        # Check if we already created a feed item for this
        existing = FeedItem.objects.filter(
            actor=instance.user,
            content_type='UserBook',
            object_id=instance.id,
            feed_type='book_finished'
        ).exists()

        if existing:
            return

        # Get all users who follow this user
        followers = Friendship.objects.filter(
            to_user=instance.user,
            status='accepted'
        ).values_list('from_user', flat=True)

        # Create feed item for each follower AND for the user themselves
        feed_items = []

        # Prepare preview text
        preview_text = f'finished reading {instance.book.title}'
        if instance.rating:
            preview_text += f' and rated it {instance.rating}/5'

        # Add feed item for the user themselves (for "My Updates")
        feed_items.append(FeedItem(
            user=instance.user,
            actor=instance.user,
            feed_type='book_finished',
            content_type='UserBook',
            object_id=instance.id,
            preview_text=preview_text,
            preview_image=instance.book.cover_image if hasattr(instance.book, 'cover_image') and instance.book.cover_image else '',
        ))

        # Add feed item for each follower
        for follower_id in followers:
            feed_items.append(FeedItem(
                user_id=follower_id,
                actor=instance.user,
                feed_type='book_finished',
                content_type='UserBook',
                object_id=instance.id,
                preview_text=preview_text,
                preview_image=instance.book.cover_image if hasattr(instance.book, 'cover_image') and instance.book.cover_image else '',
            ))

        if feed_items:
            FeedItem.objects.bulk_create(feed_items)


# ── TopicMessageLike denormalization ─────────────────────────────────

@receiver(post_save, sender=TopicMessageLike)
def increment_topic_message_likes_count(sender, instance, created, **kwargs):
    """Increment likes_count on TopicMessage when a like is created."""
    if created:
        TopicMessage.objects.filter(pk=instance.message_id).update(
            likes_count=F('likes_count') + 1
        )


@receiver(post_delete, sender=TopicMessageLike)
def decrement_topic_message_likes_count(sender, instance, **kwargs):
    """Decrement likes_count on TopicMessage when a like is deleted."""
    TopicMessage.objects.filter(pk=instance.message_id).update(
        likes_count=F('likes_count') - 1
    )


# ── Conversation last_message denormalization ────────────────────────

@receiver(post_save, sender=Message)
def update_conversation_on_message_save(sender, instance, **kwargs):
    """
    Update Conversation.last_message_at and last_message_preview when
    a message is created or edited. This replaces the inline save() override
    on the Message model to also handle edits correctly.
    """
    conversation = instance.conversation
    # Re-derive from the actual latest message (handles edits of the last msg)
    latest_msg = conversation.messages.order_by('-created_at').first()
    if latest_msg:
        conversation.last_message_at = latest_msg.created_at
        conversation.last_message_preview = latest_msg.content[:100] if latest_msg.content else ''
    else:
        conversation.last_message_at = None
        conversation.last_message_preview = ''
    conversation.save(update_fields=['last_message_at', 'last_message_preview', 'updated_at'])


@receiver(post_delete, sender=Message)
def update_conversation_on_message_delete(sender, instance, **kwargs):
    """
    Update Conversation.last_message_at and last_message_preview when
    a message is deleted, falling back to the next most recent message.
    """
    try:
        conversation = Conversation.objects.get(pk=instance.conversation_id)
    except Conversation.DoesNotExist:
        return

    latest_msg = conversation.messages.order_by('-created_at').first()
    if latest_msg:
        conversation.last_message_at = latest_msg.created_at
        conversation.last_message_preview = latest_msg.content[:100] if latest_msg.content else ''
    else:
        conversation.last_message_at = None
        conversation.last_message_preview = ''
    conversation.save(update_fields=['last_message_at', 'last_message_preview', 'updated_at'])
