"""
Check dates on UserBooks to see if finished_at and created_at are set correctly
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

# Get the right user
user = User.objects.get(email='branislav.teofilovic@gmail.com')
print(f"User: {user.email}\n")

# Check read books
read_books = UserBook.objects.filter(user=user, status='read').order_by('-finished_at')
print(f"=== READ BOOKS ({read_books.count()}) ===")
print("Checking if finished_at is set:\n")

books_with_finished = 0
books_without_finished = 0

for ub in read_books[:10]:
    if ub.finished_at:
        books_with_finished += 1
        print(f"  [OK] '{ub.book.title[:40]}' | finished_at: {ub.finished_at} | created_at: {ub.created_at.date()}")
    else:
        books_without_finished += 1
        print(f"  [MISSING] '{ub.book.title[:40]}' | finished_at: None | created_at: {ub.created_at.date()}")

print(f"\nBooks WITH finished_at: {books_with_finished}")
print(f"Books WITHOUT finished_at: {books_without_finished}")

# Check want_to_read books
print(f"\n=== WANT TO READ BOOKS ===")
want_to_read = UserBook.objects.filter(user=user, status='want_to_read').order_by('-created_at')[:5]
for ub in want_to_read:
    print(f"  '{ub.book.title[:40]}' | created_at: {ub.created_at.date()}")
