import binascii
import collections

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured

import contest.models
import qcm.models


class ContestMiddleware(object):
    def process_request(self, request):
        # General purpose queries
        events = list(contest.models.Event.objects
                      .select_related('edition')
                      .filter(edition__year=settings.PROLOGIN_EDITION))
        try:
            request.current_edition = events[0].edition
        except IndexError:
            raise ImproperlyConfigured("You need to configure at least one Edition "
                                       "and one related Event for this year ({})".format(settings.PROLOGIN_EDITION))

        events_dict = collections.defaultdict(list)
        for event in events:
            events_dict[event.type].append(event)
        events_dict = {k: v[0] if len(v) == 1
                           else sorted(v, key=lambda x: x.date_begin)
                           for k, v in events_dict.items()}
        request.current_events = {event_type.name: events_dict.get(event_type.value)
                                  for event_type in contest.models.Event.Type}

        request.current_qcm = qcm.models.Qcm.objects.filter(
            event__type=contest.models.Event.Type.qualification.value,
            event__edition=request.current_edition).first()

        # Logged-in user related queries
        request.current_contestant = None
        user = request.user
        if user.is_authenticated():
            # Create the contestant if it does not exist
            request.current_contestant, created = contest.models.Contestant.objects.get_or_create(
                user=user, edition=request.current_edition)
            if created:
                request.current_contestant.save()


class BasicAuthMiddleware(object):
    """Middleware that logs in users based on an Authorization: basic header.

    Required for Marauder to function, but it doesn't harm to keep it enabled
    for the rest of the website.
    """
    HEADER_NAME = 'HTTP_AUTHORIZATION'

    def process_request(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured('BasicAuthMiddleware should be placed '
                                       'after the AuthenticationMiddleware.')

        authorization = request.META.get(self.HEADER_NAME)
        if not authorization or ' ' not in authorization:
            return
        method, value = authorization.split(' ', 1)
        if method.lower() != 'basic':
            return
        try:
            value = binascii.a2b_base64(value)
        except binascii.Error:
            return
        value = value.decode('utf-8')
        if ':' not in value:
            return
        username, password = value.split(':', 1)

        if request.user.is_authenticated():
            if request.user.get_username() == username:
                return
            else:
                auth.logout(request)
        else:
            user = auth.authenticate(username=username, password=password)
            if user:
                request.user = user
                auth.login(request, user)
