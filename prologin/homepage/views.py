import random
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from django.views.generic import TemplateView
from zinnia.models import Entry

# PROLOGIN 2021 delete the next line when semifinals are done
from contest import event_wishes_override

import contest.models
import qcm.models
import problems.models
import sponsor.models
from contest.interschool_views import LeaderboardView


class HomepageView(TemplateView):
    template_name = 'homepage/homepage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        articles = Entry.published.prefetch_related('authors').all()[:settings.HOMEPAGE_ARTICLES]

        current_qcm = qcm.models.Qcm.full_objects.filter(
            event__type=contest.models.Event.Type.qualification.value,
            event__edition=self.request.current_edition).first()
        try:
            current_qcm_challenge = problems.models.Challenge.by_year_and_event_type(
                self.request.current_edition.year, contest.models.Event.Type.qualification)
        except ObjectDoesNotExist:
            raise ImproperlyConfigured("You must create the problem statement for edition {}"
                                       .format(settings.PROLOGIN_EDITION))
        current_contestant_qcm_problem_answers = problems.models.Submission.objects.none()

        qcm_completed = None
        if self.request.user.is_authenticated:
            current_contestant_qcm_problem_answers = problems.models.Submission.objects.filter(
                user=self.request.user, challenge=current_qcm_challenge.name)
            if current_qcm:
                qcm_completed = current_qcm.is_completed_for(self.request.current_contestant)

        problems_count = len(current_qcm_challenge.problems)
        problems_completed = current_contestant_qcm_problem_answers.count()
        context['current_qcm'] = current_qcm
        context['current_qcm_challenge'] = current_qcm_challenge
        context['current_contestant_qcm_problem_answers'] = current_contestant_qcm_problem_answers
        context['qcm_completed'] = qcm_completed
        context['problems_count'] = problems_count
        context['problems_completed'] = problems_completed
        context['born_year'] = settings.PROLOGIN_EDITION - settings.PROLOGIN_MAX_AGE
        context['articles'] = articles
        sponsors = list(sponsor.models.Sponsor.active.all())
        random.shuffle(sponsors)
        context['sponsors'] = sponsors
        leaderboard = LeaderboardView(request=self.request)
        leaderboard.request = self.request
        leaderboard.args = ()
        leaderboard.kwargs = {}
        leaderboard.get(self.request)
        context['inter_school_leaderboard'] = leaderboard.get_queryset()

        # ADDED FOR PROLOGIN2021 SEMIFINALS WISH OVERRIDES - DELETE IT LATER
        if self.request.user.is_authenticated:
            context['wish_override'] = event_wishes_override.get_wish_override_context(self.request.current_data.current_contestant)

        return context
