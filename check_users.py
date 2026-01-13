"""
Check all users and their book counts
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

User = get_user_model()

print("=== ALL USERS AND THEIR BOOKS ===\n")

all_users = User.objects.all()
for user in all_users:
    book_count = UserBook.objects.filter(user=user).count()
    print(f"User ID: {user.id} | Email: {user.email} | Books: {book_count}")

print(f"\n=== USERBOOK BREAKDOWN ===")
total_userbooks = UserBook.objects.count()
print(f"Total UserBook entries: {total_userbooks}")

# Check for duplicates across all users
from django.db.models import Count
duplicates = UserBook.objects.values('user_id', 'book_id').annotate(count=Count('id')).filter(count__gt=1)
print(f"Duplicate user+book combinations: {duplicates.count()}")

if duplicates.count() > 0:
    print("\nShowing duplicates:")
    for dup in duplicates[:10]:
        user = User.objects.get(id=dup['user_id'])
        entries = UserBook.objects.filter(user_id=dup['user_id'], book_id=dup['book_id']).select_related('book')
        print(f"\n  User: {user.email} | Book ID: {dup['book_id']} | Count: {dup['count']}")
        for entry in entries:
            print(f"    - UserBook ID: {entry.id} | Title: {entry.book.title[:50]} | Status: {entry.status} | Updated: {entry.updated_at}")
