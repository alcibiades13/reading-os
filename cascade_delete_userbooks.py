"""
CASCADE delete all related data and then UserBooks
"""
import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== CASCADE DELETING ALL USERBOOKS AND RELATED DATA ===\n")

# Get the RIGHT user
user = User.objects.get(email='branislav.teofilovic@gmail.com')
print(f"User: {user.email} (ID: {user.id})\n")

with connection.cursor() as cursor:
    # Count before
    cursor.execute("SELECT COUNT(*) FROM reading_userbook WHERE user_id = %s", [user.id])
    before_count = cursor.fetchone()[0]
    print(f"UserBooks before delete: {before_count}")

    # Get all UserBook IDs for this user
    cursor.execute("SELECT id FROM reading_userbook WHERE user_id = %s", [user.id])
    userbook_ids = [row[0] for row in cursor.fetchall()]
    print(f"Found {len(userbook_ids)} UserBook IDs to delete")

    if userbook_ids:
        # Step 1: Delete quote tags first
        cursor.execute("""
            DELETE FROM reading_quote_tags
            WHERE quote_id IN (
                SELECT id FROM reading_quote
                WHERE user_book_id = ANY(%s)
            )
        """, [userbook_ids])
        print(f"Deleted {cursor.rowcount} quote tags")

        # Step 2: Delete quotes
        cursor.execute("""
            DELETE FROM reading_quote
            WHERE user_book_id = ANY(%s)
        """, [userbook_ids])
        print(f"Deleted {cursor.rowcount} quotes")

        # Step 3: Delete ALL feed items for this user (simplest approach)
        cursor.execute("DELETE FROM social_feeditem WHERE user_id = %s", [user.id])
        print(f"Deleted {cursor.rowcount} feed items")

        # Step 4: NOW delete UserBooks
        cursor.execute("DELETE FROM reading_userbook WHERE user_id = %s", [user.id])
        deleted = cursor.rowcount
        print(f"Deleted {deleted} UserBooks")

    # Count after
    cursor.execute("SELECT COUNT(*) FROM reading_userbook WHERE user_id = %s", [user.id])
    after_count = cursor.fetchone()[0]
    print(f"UserBooks after delete: {after_count}")

print(f"\n=== READY FOR CLEAN RE-IMPORT ===")
print("Now import the Goodreads CSV through the web interface.")
