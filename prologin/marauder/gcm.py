import requests

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import translation

from marauder.models import UserProfile
from users.models import ProloginUser


def multicast_notification(recipients,
                           title_format: str,
                           message_format: str,
                           format_data={}):
    """
    Sends a notification to a group of Marauder users (provided as an iterable
    of UserProfile). The title and the message of the notification are
    localized for each recipient user and formatted using
    .format(**format_data).

    Returns:
        (number of notifications successfully sent, total number of recipients)
    """
    successful_recipients = total_recipients = 0
    for recipient in recipients:
        total_recipients += 1
        try:
            unicast_notification(recipient, title_format, message_format,
                                 format_data)
            successful_recipients += 1
        except ValueError:
            pass
    return (total_recipients, successful_recipients)


def unicast_notification(to: UserProfile,
                         title_format: str,
                         message_format: str,
                         format_data={}):
    """
    Sends a notification to a given Marauder user. The title and the message of
    the notification are localized for the recipient user and formatted using
    .format(**format_data).

    Raises:
        ValueError: If the recipient does not have GCM data.
    """
    title = _translate_for(title_format, to.user).format(**format_data)
    message = _translate_for(message_format, to.user).format(**format_data)
    _push_message(to.gcm_token, {"title": title, "message": message})


def _translate_for(message: str, recipient: ProloginUser):
    """
    Translates a message for the locale of a given user. TODO: Move this to a
    more appropriate module.
    """
    with translation.override(recipient.preferred_locale):
        return translation.ugettext(message)


def _push_message(to: str, data: dict, **kwargs):
    """
    Internal function to push a message to a device through Google Cloud
    Messaging.
    """
    if not to:
        raise ValueError("Recipient can not be empty")
    if not isinstance(data, dict):
        raise TypeError("Data must be a dict")
    if not settings.MARAUDER_GCM_KEY:
        raise ImproperlyConfigured("No GCM key configured.")
    return requests.post(
        'https://gcm-http.googleapis.com/gcm/send',
        headers={'Authorization': 'key=' + settings.MARAUDER_GCM_KEY},
        json={'to': to,
              'data': data},
        **kwargs).ok
