"""
DELETE all UserBooks for the main user and prepare for clean re-import
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

print("=== DELETING ALL USERBOOKS FOR CLEAN RE-IMPORT ===\n")

# Get the RIGHT user
user = User.objects.get(email='branislav.teofilovic@gmail.com')
print(f"User: {user.email}\n")

# Count before delete
before_count = UserBook.objects.filter(user=user).count()
print(f"UserBooks before delete: {before_count}")

# DELETE ALL
UserBook.objects.filter(user=user).delete()

# Verify
after_count = UserBook.objects.filter(user=user).count()
print(f"UserBooks after delete: {after_count}")

print(f"\n=== READY FOR CLEAN RE-IMPORT ===")
print("Now import the Goodreads CSV through the web interface.")
