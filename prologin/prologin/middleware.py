from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import contest.models
import qcm.models
import problems.models


class ContestMiddleware(object):
    def process_request(self, request):
        user = request.user
        today = timezone.now().date()
        request.current_edition = contest.models.Edition.objects.prefetch_related('events').get(year=settings.PROLOGIN_EDITION)
        request.current_events = request.current_edition.events.filter(date_begin__lte=today, date_end__gte=today)
        request.current_qualification = request.current_edition.events.filter(type=contest.models.Event.Type.qualification.value).first()
        request.current_regionales = request.current_edition.events.filter(type=contest.models.Event.Type.regionale.value).order_by('date_begin')
        request.current_finale = request.current_edition.events.filter(type=contest.models.Event.Type.finale.value).first()
        request.current_qcm = qcm.models.Qcm.objects.filter(
            event__type=contest.models.Event.Type.qualification.value,
            event__edition=request.current_edition).first()
        request.current_qcm_problems = problems.models.Challenge.objects.filter(
            event__type=contest.models.Event.Type.qualification.value,
            event__edition=request.current_edition)

        request.current_contestant = None
        request.current_contestant_qcm_problem_answers = problems.models.Answer.objects.none()

        if user.is_authenticated():
            try:
                request.current_contestant = user.contestants.distinct().get(edition=request.current_edition)
            except ObjectDoesNotExist:
                request.current_contestant = contest.models.Contestant(user=user, edition=request.current_edition)
                request.current_contestant.save()
            request.current_contestant_qcm_problem_answers = problems.models.Answer.objects.filter(
                challenge__event__edition=request.current_edition,
                contestant=request.current_contestant,
                is_final=True,
            )
