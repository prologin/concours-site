from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import contest.models
import qcm.models


class ContestMiddleware(object):
    def process_request(self, request):
        user = request.user
        today = timezone.now().date()
        request.current_edition = contest.models.Edition.objects.prefetch_related('events').get(year=settings.PROLOGIN_EDITION)
        request.current_events = request.current_edition.events.filter(date_begin__lte=today, date_end__gte=today)
        request.current_qcm = qcm.models.Qcm.objects.filter(event__edition=request.current_edition).first()
        if user.is_authenticated():
            try:
                request.current_contestant = user.contestants.distinct().get(edition=request.current_edition)
            except ObjectDoesNotExist:
                request.current_contestant = contest.models.Contestant(user=user, edition=request.current_edition)
                request.current_contestant.save()
