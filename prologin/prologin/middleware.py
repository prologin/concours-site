from django.conf import settings
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

        events_dict = {event.type: event for event in events}
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
