from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.reading.models import Quote, UserBook
from apps.social.models import FeedItem, Friendship

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate feed items from existing quotes and user books'

    def handle(self, *args, **options):
        self.stdout.write('Populating feed items...')

        # Clear existing feed items
        FeedItem.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared existing feed items'))

        # Create feed items for all public quotes
        quotes_count = 0
        for quote in Quote.objects.filter(is_public=True):
            # Get all users who follow this user
            followers = Friendship.objects.filter(
                to_user=quote.user,
                status='accepted'
            ).values_list('from_user', flat=True)

            feed_items = []

            # Add feed item for the user themselves (for "My Updates")
            feed_items.append(FeedItem(
                user=quote.user,
                actor=quote.user,
                feed_type='quote_added',
                content_type='Quote',
                object_id=quote.id,
                preview_text=f'"{quote.text[:200]}..." - {quote.book_title}',
                preview_image='',
            ))

            # Add feed item for each follower
            for follower_id in followers:
                feed_items.append(FeedItem(
                    user_id=follower_id,
                    actor=quote.user,
                    feed_type='quote_added',
                    content_type='Quote',
                    object_id=quote.id,
                    preview_text=f'"{quote.text[:200]}..." - {quote.book_title}',
                    preview_image='',
                ))

            if feed_items:
                FeedItem.objects.bulk_create(feed_items)
                quotes_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created feed items for {quotes_count} quotes'))

        # Create feed items for all finished books
        books_count = 0
        for user_book in UserBook.objects.filter(status='read', finished_at__isnull=False):
            # Check if we already created a feed item for this
            existing = FeedItem.objects.filter(
                actor=user_book.user,
                content_type='UserBook',
                object_id=user_book.id,
                feed_type='book_finished'
            ).exists()

            if existing:
                continue

            # Get all users who follow this user
            followers = Friendship.objects.filter(
                to_user=user_book.user,
                status='accepted'
            ).values_list('from_user', flat=True)

            # Create feed item for each follower AND for the user themselves
            feed_items = []

            # Prepare preview text
            preview_text = f'finished reading {user_book.book.title}'
            if user_book.rating:
                preview_text += f' and rated it {user_book.rating}/5'

            # Add feed item for the user themselves (for "My Updates")
            feed_items.append(FeedItem(
                user=user_book.user,
                actor=user_book.user,
                feed_type='book_finished',
                content_type='UserBook',
                object_id=user_book.id,
                preview_text=preview_text,
                preview_image=user_book.book.cover_image if hasattr(user_book.book, 'cover_image') and user_book.book.cover_image else '',
            ))

            # Add feed item for each follower
            for follower_id in followers:
                feed_items.append(FeedItem(
                    user_id=follower_id,
                    actor=user_book.user,
                    feed_type='book_finished',
                    content_type='UserBook',
                    object_id=user_book.id,
                    preview_text=preview_text,
                    preview_image=user_book.book.cover_image if hasattr(user_book.book, 'cover_image') and user_book.book.cover_image else '',
                ))

            if feed_items:
                FeedItem.objects.bulk_create(feed_items)
                books_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created feed items for {books_count} finished books'))

        total_feed_items = FeedItem.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Total feed items: {total_feed_items}'))
        self.stdout.write(self.style.SUCCESS('Done!'))
