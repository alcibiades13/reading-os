import os
import sys
import django
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.social.models import FeedItem
from apps.social.serializers import FeedItemSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# Test for user 1 (branislav)
user1 = User.objects.get(id=1)
feed_items_user1 = FeedItem.objects.filter(user=user1).order_by('-created_at')
serializer_user1 = FeedItemSerializer(feed_items_user1, many=True)

print("=" * 80)
print(f"USER 1 ({user1.email}) - FEED API RESPONSE")
print("=" * 80)
print(f"Total items: {feed_items_user1.count()}")
print(f"\nFirst 3 items (serialized):")
print(json.dumps(serializer_user1.data[:3], indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("ANALYZING ITEMS:")
print("=" * 80)
for item in feed_items_user1[:5]:
    print(f"ID={item.id}, actor_id={item.actor.id} ({item.actor.email}), feed_type={item.feed_type}")

own_items = feed_items_user1.filter(actor=user1)
other_items = feed_items_user1.exclude(actor=user1)

print(f"\nOwn items (actor=user1): {own_items.count()}")
print(f"Other items (actor!=user1): {other_items.count()}")
