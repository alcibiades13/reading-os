from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.reading.models import Quote, UserBook
from apps.social.models import FeedItem, Friendship

User = get_user_model()

# Store previous state of UserBook before save
_userbook_pre_save_state = {}


@receiver(pre_save, sender=UserBook)
def store_userbook_pre_save_state(sender, instance, **kwargs):
    """Store the previous state of UserBook before saving"""
    if instance.pk:
        try:
            old_instance = UserBook.objects.get(pk=instance.pk)
            _userbook_pre_save_state[instance.pk] = {
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

    # Get previous state
    old_state = _userbook_pre_save_state.get(instance.pk, {})
    old_status = old_state.get('status')
    old_page = old_state.get('current_page')

    # Clean up the stored state
    if instance.pk in _userbook_pre_save_state:
        del _userbook_pre_save_state[instance.pk]

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
