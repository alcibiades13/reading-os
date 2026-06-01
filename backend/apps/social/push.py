"""
FCM push notification utility.
Requires FIREBASE_SERVER_KEY in settings (from Firebase Console → Cloud Messaging).
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

FCM_URL = 'https://fcm.googleapis.com/fcm/send'


def send_push_to_user(user, title: str, body: str, data: dict = None):
    """
    Send a push notification to all registered devices of a user.
    Silently skips if FIREBASE_SERVER_KEY is not configured.
    """
    server_key = getattr(settings, 'FIREBASE_SERVER_KEY', '')
    if not server_key:
        return

    from apps.social.models import DevicePushToken
    tokens = list(DevicePushToken.objects.filter(user=user).values_list('token', flat=True))
    if not tokens:
        return

    _send_multicast(tokens, title, body, data or {})


def _send_multicast(tokens: list, title: str, body: str, data: dict):
    server_key = settings.FIREBASE_SERVER_KEY
    headers = {
        'Authorization': f'key={server_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'registration_ids': tokens,
        'notification': {
            'title': title,
            'body': body,
            'sound': 'default',
        },
        'data': data,
    }
    try:
        resp = requests.post(FCM_URL, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        result = resp.json()

        # Remove invalid tokens
        if result.get('failure', 0) > 0:
            from apps.social.models import DevicePushToken
            results = result.get('results', [])
            invalid = [
                tokens[i] for i, r in enumerate(results)
                if r.get('error') in ('InvalidRegistration', 'NotRegistered')
            ]
            if invalid:
                DevicePushToken.objects.filter(token__in=invalid).delete()

    except Exception as e:
        logger.error(f'FCM push failed: {e}')
