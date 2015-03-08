from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
import contest.models

class ContestMiddleware(object):
    def process_request(self, request):
        user = request.user
        if user.is_authenticated():
            try:
                request.current_contestant = user.contestants.distinct().get(edition__year=settings.PROLOGIN_EDITION)
            except ObjectDoesNotExist:
                request.current_contestant = contest.models.Contestant(
                    user=user,
                    edition=contest.models.Edition.objects.get(year=settings.PROLOGIN_EDITION),
                )
                request.current_contestant.save()
