"""
Script to remove duplicate UserBook entries for the same user and book.
Keeps only the MOST RECENT entry (by updated_at) for each user+book combination.
"""
import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.reading.models import UserBook
from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()

print("=== REMOVING DUPLICATE USERBOOKS ===\n")

# Get user
user = User.objects.first()
print(f"User: {user.email}\n")

# Find duplicates: same user + book combination
print("Finding duplicates...\n")

# Get all UserBooks for this user
all_user_books = UserBook.objects.filter(user=user).select_related('book').order_by('book_id', '-updated_at')

# Track which book IDs we've seen
seen_books = set()
duplicates_removed = 0

for ub in all_user_books:
    if ub.book_id in seen_books:
        # This is a duplicate - DELETE IT
        print(f"  REMOVING DUPLICATE: UserBook ID {ub.id} for '{ub.book.title}' (Book ID: {ub.book_id})")
        ub.delete()
        duplicates_removed += 1
    else:
        # First time seeing this book - KEEP IT
        seen_books.add(ub.book_id)

print(f"\n=== SUMMARY ===")
print(f"Duplicates removed: {duplicates_removed}")
print(f"Unique books remaining: {len(seen_books)}")
print(f"\nDone!")
