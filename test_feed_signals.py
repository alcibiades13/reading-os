import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.reading.models import UserBook, Book
from apps.social.models import FeedItem
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

# Get user
user = User.objects.first()
print(f"User: {user.email}")

# Get a book
book = Book.objects.first()
print(f"Book: {book.title}")

# Create a new UserBook with currently_reading status
print("\nCreating new currently_reading UserBook...")
user_book = UserBook.objects.create(
    user=user,
    book=book,
    status='currently_reading',
    started_at=datetime.now()
)
print(f"Created UserBook ID: {user_book.id}")

# Check if feed items were created
feed_items = FeedItem.objects.filter(feed_type='book_started')
print(f"\nbook_started feed items: {feed_items.count()}")
for item in feed_items:
    print(f"  - {item.preview_text}")

# Now test progress update
print("\n\nTesting progress update...")
user_book.current_page = 100
user_book.save()
print(f"Updated current_page to 100")

progress_items = FeedItem.objects.filter(feed_type='progress_update')
print(f"\nprogress_update feed items: {progress_items.count()}")
for item in progress_items:
    print(f"  - {item.preview_text}")
