import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.social.models import FeedItem
from apps.social.serializers import FeedItemSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# Test for user 1
user1 = User.objects.get(id=1)
feed_items = FeedItem.objects.filter(user=user1).order_by('-created_at')

print(f"Total feed items for user 1: {feed_items.count()}")
print(f"\nFirst 3 items:")
for item in feed_items[:3]:
    print(f"  ID={item.id}, actor_id={item.actor.id}, feed_type={item.feed_type}")

# Now serialize
serializer = FeedItemSerializer(feed_items, many=True)
print(f"\nSerialized data length: {len(serializer.data)}")
print(f"First item keys: {serializer.data[0].keys() if serializer.data else 'NO DATA'}")
