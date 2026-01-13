from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.reading.models import Quote, UserBook
from apps.social.models import FeedItem, Friendship

User = get_user_model()


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

    # Handle book started (currently_reading status and has started_at)
    if instance.status == 'currently_reading' and instance.started_at and created:
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

    # Handle progress update (currently_reading with current_page)
    if instance.status == 'currently_reading' and instance.current_page and not created:
        # Only create progress updates for significant milestones (every 25%)
        total_pages = instance.book.pages if hasattr(instance.book, 'pages') and instance.book.pages else 0
        if total_pages > 0:
            progress_percent = (instance.current_page / total_pages) * 100
            # Only create at 25%, 50%, 75% milestones
            if progress_percent >= 25 and progress_percent % 25 <= 5:  # Allow 5% tolerance
                # Check if we already created this progress milestone
                existing_progress = FeedItem.objects.filter(
                    actor=instance.user,
                    content_type='UserBook',
                    object_id=instance.id,
                    feed_type='progress_update',
                    preview_text__contains=f'{int(progress_percent)}%'
                ).exists()

                if not existing_progress:
                    feed_items = []
                    preview_text = f'made {int(progress_percent)}% progress on {instance.book.title}'

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
