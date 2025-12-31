#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify progress update creates feed items
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.reading.models import UserBook
from apps.social.models import FeedItem
from django.contrib.auth import get_user_model

User = get_user_model()

# Get a test user and their book
user = User.objects.first()
if not user:
    print("No users found in database")
    sys.exit(1)

user_book = UserBook.objects.filter(user=user).first()
if not user_book:
    print(f"No books found for user {user.username}")
    sys.exit(1)

print(f"Testing progress update for: {user_book.book.title}")
print(f"Current page: {user_book.current_page}")

# Count feed items before
feed_count_before = FeedItem.objects.filter(user=user, feed_type='progress_update').count()
print(f"Feed items before: {feed_count_before}")

# Update progress
old_page = user_book.current_page or 0
new_page = old_page + 10
user_book.current_page = new_page
user_book.save(update_fields=['current_page'])

print(f"Updated current_page from {old_page} to {new_page}")

# Count feed items after
feed_count_after = FeedItem.objects.filter(user=user, feed_type='progress_update').count()
print(f"Feed items after: {feed_count_after}")

if feed_count_after > feed_count_before:
    latest_feed = FeedItem.objects.filter(user=user, feed_type='progress_update').latest('created_at')
    print(f"\nSUCCESS! New feed item created:")
    print(f"  Type: {latest_feed.feed_type}")
    print(f"  Preview: {latest_feed.preview_text}")
else:
    print(f"\nFAILED! No new feed item created")
