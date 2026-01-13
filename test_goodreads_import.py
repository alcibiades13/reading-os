import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.books.models import Book
from apps.reading.models import UserBook
from django.contrib.auth import get_user_model

User = get_user_model()

# Get user
user = User.objects.first()
print(f"User: {user.email}")

# Check imported books
print("\n=== IMPORTED BOOKS ===")
user_books = UserBook.objects.filter(user=user).select_related('book')
print(f"Total books in library: {user_books.count()}")

# Check by status
statuses = ['want_to_read', 'currently_reading', 'read', 'abandoned']
for status in statuses:
    count = user_books.filter(status=status).count()
    print(f"  {status}: {count}")

# Check books with covers
books_with_covers = user_books.filter(book__cover_image__isnull=False).exclude(book__cover_image='').count()
print(f"\nBooks with covers: {books_with_covers}/{user_books.count()}")

# Check books with ratings
books_with_ratings = user_books.filter(rating__isnull=False).exclude(rating=0)
print(f"\nBooks with ratings: {books_with_ratings.count()}")
for ub in books_with_ratings[:5]:
    print(f"  {ub.book.title}: {ub.rating}/10")

# Sample book details
print("\n=== SAMPLE BOOKS ===")
for ub in user_books[:3]:
    print(f"\nTitle: {ub.book.title}")
    print(f"Author: {', '.join([a.name for a in ub.book.authors.all()])}")
    print(f"Status: {ub.status}")
    print(f"Rating: {ub.rating}/10" if ub.rating else "Rating: Not rated")
    print(f"Cover: {ub.book.cover_image[:80] if ub.book.cover_image else 'No cover'}")
