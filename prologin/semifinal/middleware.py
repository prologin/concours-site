# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist

import contest.models
import problems.models


class SemifinalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _raise(self):
        raise ImproperlyConfigured("You need to create/configure a single Edition and related regional event Event "
                                   "for year {}.".format(settings.PROLOGIN_EDITION))

    def __call__(self, request):
        year = settings.PROLOGIN_EDITION
        # Current semifinal event
        event = (contest.models.Event.objects
                 .select_related('edition')
                 .filter(edition__year=year)
                 .first())

        if event is None:
            self._raise()

        request.current_event = event

        try:
            request.current_edition = event.edition
        except IndexError:
            self._raise()

        try:
            request.current_challenge = (problems.models.Challenge
                                         .by_year_and_event_type(year, contest.models.Event.Type.semifinal))
        except ObjectDoesNotExist:
            raise ImproperlyConfigured("There is no challenge for regional event year {}".format(year))

        # Logged-in user related queries
        request.current_contestant = None
        user = request.user
        if user.is_authenticated:
            # Create the contestant if it does not exist
            request.current_contestant, created = (contest.models.Contestant.objects
                                                   .get_or_create(user=user, edition=request.current_edition))
            if created:
                request.current_contestant.save()

        return self.get_response(request)
