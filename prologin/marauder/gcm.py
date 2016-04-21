import requests

from django.conf import settings


def push_message(to: str, data: dict, **kwargs):
    """
    Push a message to a device through Google Cloud Messaging.
    """
    if not to:
        raise ValueError("Recipient can not be empty")
    if not isinstance(data, dict):
        raise TypeError("Data must be a dict")
    return requests.post(
        'https://gcm-http.googleapis.com/gcm/send',
        headers={'Authorization': 'key=' + settings.MARAUDER_GCM_KEY},
        json={'to': to,
              'data': data},
        **kwargs).ok
