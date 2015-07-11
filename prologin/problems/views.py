from django.views.generic import TemplateView, RedirectView
from django.http import Http404
from django.db.models import Count
from django.conf import settings

from django.core.urlresolvers import reverse

from problems.forms import SearchForm
from contest.models import Event
import problems.models


class Index(TemplateView):
    template_name = 'problems/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['challenges'] = [c for c in problems.models.Challenge.all() if c.displayable]
        context['search_form'] = SearchForm()
        return context


class Challenge(TemplateView):
    template_name = 'problems/challenge.html'
    # Event code → (tup, challenge prefix)
    event_category_mapping = {
        Event.Type.qualification.name: (Event.Type.qualification, 'qcm'),
        Event.Type.semifinal.name: (Event.Type.semifinal, 'demi'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = context['year'] = int(self.kwargs['year'])
        event_type = Event.Type[self.kwargs['type']]
        context['challenge'] = challenge = problems.models.Challenge.by_year_and_event_type(year, event_type)
        if not challenge.displayable:
            raise Http404()

        context['problems'] = sorted(challenge.problems, key=lambda p: p.difficulty)

        challenge_score = 0
        challenge_done = 0

        for problem in context['problems']:
            # Monkey-patch the problem to add the progressbar width percentage
            problem.percentage_level = int(problem.difficulty / settings.PROLOGIN_MAX_LEVEL_DIFFICULTY * 100)

        if self.request.user.is_authenticated():
            # To display user scores on each problem
            submissions = (problems.models.Submission.objects
                           .filter(user=self.request.user, challenge=challenge.name)
                           .select_related('codes')
                           .annotate(code_count=Count('codes')))
            submissions = {sub.problem: sub for sub in submissions}
            for problem in context['problems']:
                # Monkey-patch the problem to add the submission object
                submission = submissions.get(problem.name)
                problem.submission = submission
                if submission:
                    challenge_score += submission.score()
                    if submission.succeeded():
                        challenge_done += 1

        context['challenge_score'] = challenge_score
        context['challenge_done'] = challenge_done == len(challenge.problems)

        return context


class LegacyChallengeRedirect(RedirectView):
    mapping = {
        'qcm': Event.Type.qualification,
        'demi': Event.Type.semifinal,
    }

    def get_redirect_url(self, *args, **kwargs):
        event_type = LegacyChallengeRedirect.mapping[self.kwargs['type']].name
        return reverse('training:challenge', kwargs={'type': event_type, 'year': self.kwargs['year']})
