#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test to verify UserBook serializer includes current_page
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.reading.models import UserBook
from apps.reading.serializers import UserBookListSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# Get a test user and their book
user = User.objects.first()
if not user:
    print("No users found")
    sys.exit(1)

user_book = UserBook.objects.filter(user=user).first()
if not user_book:
    print(f"No books found for user {user.username}")
    sys.exit(1)

print(f"Testing UserBook: {user_book.book.title}")
print(f"Current page in DB: {user_book.current_page}")

# Serialize it
serializer = UserBookListSerializer(user_book)
data = serializer.data

print(f"\nSerialized data:")
print(f"  Has 'current_page' field: {'current_page' in data}")
if 'current_page' in data:
    print(f"  current_page value: {data['current_page']}")
else:
    print(f"  Available fields: {list(data.keys())}")

# Now test updating
print(f"\nUpdating current_page to 100...")
user_book.current_page = 100
user_book.save(update_fields=['current_page'])

# Serialize again
serializer = UserBookListSerializer(user_book)
data = serializer.data
print(f"After update:")
print(f"  current_page in serializer: {data.get('current_page')}")
print(f"  current_page in DB: {user_book.current_page}")
