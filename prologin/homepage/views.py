from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from django.views.generic import TemplateView
from zinnia.models import Entry

import contest.models
import qcm.models
import problems.models


class HomepageView(TemplateView):
    template_name = 'homepage/homepage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        articles = Entry.published.prefetch_related('authors').all()[:settings.HOMEPAGE_ARTICLES]

        current_qcm = qcm.models.Qcm.objects.filter(
            event__type=contest.models.Event.Type.qualification.value,
            event__edition=self.request.current_edition).first()
        try:
            # FIXME: this is *training* challenge! not contest!
            current_qcm_challenge = problems.models.Challenge.by_year_and_event_type(
                self.request.current_edition.year, contest.models.Event.Type.qualification)
        except ObjectDoesNotExist:
            raise ImproperlyConfigured("You must create the problem statement for edition {}"
                                       .format(settings.PROLOGIN_EDITION))
        # FIXME: this is *training* challenge! not contest!
        current_contestant_qcm_problem_answers = problems.models.Submission.objects.none()

        qcm_completed = None
        if self.request.user.is_authenticated():
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
        return context
