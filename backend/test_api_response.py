#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test API response for UserBook update
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.reading.models import UserBook
import json

User = get_user_model()
client = Client()

# Get test user
user = User.objects.first()
if not user:
    print("No users found")
    sys.exit(1)

# Login
response = client.post('/api/auth/login/', {
    'username': user.username,
    'password': 'admin123'  # Assuming this is the password
}, content_type='application/json')

if response.status_code != 200:
    print(f"Login failed: {response.status_code}")
    print(response.content)
    sys.exit(1)

token = response.json()['access']
print(f"Logged in as {user.username}")

# Get user's book
user_book = UserBook.objects.filter(user=user).first()
if not user_book:
    print("No user books found")
    sys.exit(1)

print(f"\nTesting update for: {user_book.book.title}")
print(f"Current page before: {user_book.current_page}")

# Update via API
update_data = {'current_page': 150}
response = client.patch(
    f'/api/reading/user-books/{user_book.id}/',
    data=json.dumps(update_data),
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Bearer {token}'
)

print(f"\nAPI Response Status: {response.status_code}")
print(f"Response body:")
response_data = response.json()
print(json.dumps(response_data, indent=2))

print(f"\nHas 'current_page' in response: {'current_page' in response_data}")
if 'current_page' in response_data:
    print(f"Response current_page: {response_data['current_page']}")

# Check DB
user_book.refresh_from_db()
print(f"\nCurrent page in DB after update: {user_book.current_page}")
