"""
Force delete all UserBooks using raw SQL to avoid signal issues
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

print("=== FORCE DELETING ALL USERBOOKS ===\n")

# Get the RIGHT user
user = User.objects.get(email='branislav.teofilovic@gmail.com')
print(f"User: {user.email} (ID: {user.id})\n")

# Use raw SQL to delete without triggering signals
with connection.cursor() as cursor:
    # Count before
    cursor.execute("SELECT COUNT(*) FROM reading_userbook WHERE user_id = %s", [user.id])
    before_count = cursor.fetchone()[0]
    print(f"UserBooks before delete: {before_count}")

    # DELETE ALL for this user
    cursor.execute("DELETE FROM reading_userbook WHERE user_id = %s", [user.id])
    deleted = cursor.rowcount

    print(f"Deleted: {deleted} UserBooks")

    # Count after
    cursor.execute("SELECT COUNT(*) FROM reading_userbook WHERE user_id = %s", [user.id])
    after_count = cursor.fetchone()[0]
    print(f"UserBooks after delete: {after_count}")

print(f"\n=== READY FOR CLEAN RE-IMPORT ===")
print("Now import the Goodreads CSV through the web interface.")
