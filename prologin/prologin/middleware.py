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
        request.current_edition = contest.models.Edition.objects.prefetch_related('events').get(
            year=settings.PROLOGIN_EDITION)
        request.current_events = request.current_edition.events.filter(date_begin__lte=today, date_end__gte=today)
        request.current_qualification = request.current_edition.events.filter(
            type=contest.models.Event.Type.qualification.value).first()
        request.current_semifinal = request.current_edition.events.filter(
            type=contest.models.Event.Type.semifinal.value).order_by('date_begin')
        request.current_finale = request.current_edition.events.filter(
            type=contest.models.Event.Type.final.value).first()
        request.current_qcm = qcm.models.Qcm.objects.filter(
            event__type=contest.models.Event.Type.qualification.value,
            event__edition=request.current_edition).first()
        request.current_qcm_challenge = problems.models.Challenge.by_year_and_event_type(
            request.current_edition.year, contest.models.Event.Type.qualification)

        request.current_contestant = None
        request.current_contestant_qcm_problem_answers = problems.models.Submission.objects.none()

        if user.is_authenticated():
            try:
                request.current_contestant = user.contestants.distinct().get(edition=request.current_edition)
            except ObjectDoesNotExist:
                request.current_contestant = contest.models.Contestant(user=user, edition=request.current_edition)
                request.current_contestant.save()
                request.current_contestant_qcm_problem_answers = problems.models.Submission.objects.filter(
                    user=user, challenge=request.current_qcm_challenge.name
                )
