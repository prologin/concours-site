import collections
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.wsgi import WSGIRequest
from django.utils.functional import cached_property

import contest.models
import qcm.models


class Data:
    def __init__(self, request):
        self.request = request

    @cached_property
    def events(self):
        return list(contest.models.Event.objects
                    .select_related('edition')
                    .filter(edition__year=settings.PROLOGIN_EDITION))

    @cached_property
    def edition(self):
        try:
            return self.events[0].edition
        except IndexError:
            raise ImproperlyConfigured("You need to configure at least one Edition "
                                       "and one related Event for this year ({})".format(settings.PROLOGIN_EDITION))

    @cached_property
    def current_events(self):
        events_dict = collections.defaultdict(list)
        for event in self.events:
            events_dict[contest.models.Event.Type(event.type).name].append(event)
        events_dict = {k: v[0] if len(v) == 1 else sorted(v, key=lambda x: x.date_begin)
                       for k, v in events_dict.items()}
        return events_dict

    @cached_property
    def current_qcm(self):
        return qcm.models.Qcm.objects.filter(
            event__type=contest.models.Event.Type.qualification.value,
            event__edition=self.edition).first()

    @cached_property
    def current_contestant(self):
        current_contestant = None
        user = self.request.user
        if user.is_authenticated():
            # Create the contestant if it does not exist
            current_contestant, created = contest.models.Contestant.objects.get_or_create(
                user=user, edition=self.edition)
            if created:
                current_contestant.save()
        return current_contestant


class ContestMiddleware(object):
    def process_request(self, request):
        # Warning: terrible hack ahead.
        # Attach a custom attribute getter on WSGIRequest to lazy-load
        # current edition data. Saves many queries on every page load.

        def __getattr__(this, attr):
            if attr == 'current_edition':
                return this.current_data.edition
            if attr == 'current_events':
                return this.current_data.current_events
            if attr == 'current_qcm':
                return this.current_data.current_qcm
            if attr == 'current_contestant':
                return this.current_data.current_contestant
            return super(WSGIRequest, this).__getattr__(attr)

        WSGIRequest.__getattr__ = __getattr__
        request.current_data = Data(request)
