import os
import sys
import django

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.social.models import FeedItem
from django.contrib.auth import get_user_model

User = get_user_model()

# Check both users
for user_id in [1, 2]:
    user = User.objects.get(id=user_id)
    print(f'\n{"=" * 80}')
    print(f'User ID: {user.id}, Email: {user.email}')
    print(f'{"=" * 80}')

    # Get all feed items for this user
    feed_items = FeedItem.objects.filter(user=user).order_by('-created_at')
    print(f'\nTotal FeedItems where user={user.id} (as recipient): {feed_items.count()}')

    # Check how many are from the user themselves
    own_items = feed_items.filter(actor=user)
    print(f'\nFeedItems where actor=user (MY UPDATES should show): {own_items.count()}')
    if own_items.count() > 0:
        print('First 5:')
        for item in own_items[:5]:
            print(f'  ID={item.id}, type={item.feed_type}')

    # Check how many are from others
    other_items = feed_items.exclude(actor=user)
    print(f'\nFeedItems where actor!=user (FOLLOWING should show): {other_items.count()}')
    if other_items.count() > 0:
        print('First 5:')
        for item in other_items[:5]:
            print(f'  ID={item.id}, actor_id={item.actor.id}, type={item.feed_type}')
