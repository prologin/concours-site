from django.views.generic import TemplateView, RedirectView
from django.http import Http404
from django.db.models import Count
from django.conf import settings

from django.core.urlresolvers import reverse

from problems.problem import list_challenges, get_challenge

from problems.forms import SearchForm
from problems.models import Submission
from prologin.utils import cached
from problems import QUALIFICATION_TUP, REGIONAL_TUP

CACHE_KEY_CHALLENGE_LIST = 'problems.index.challenges'


class Index(TemplateView):
    template_name = 'problems/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenges = cached(list_challenges, 'challenge_list')
        context['challenges'] = challenges
        context['search_form'] = SearchForm()
        return context


class Challenge(TemplateView):
    template_name = 'problems/challenge.html'
    # Event code → (tup, challenge prefix)
    event_category_mapping = {
        QUALIFICATION_TUP.code: (QUALIFICATION_TUP, 'qcm'),
        REGIONAL_TUP.code: (REGIONAL_TUP, 'demi'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_type, path_prefix = Challenge.event_category_mapping[self.kwargs['type']]
        year = context['year'] = int(self.kwargs['year'])
        challenge_name = '{}{}'.format(path_prefix, year)
        challenge = cached(
            lambda: get_challenge(challenge_name, with_subject=True, with_problem_props=True, with_problem_data=False),
            'challenge_details',
            name=challenge_name)
        context['challenge'] = challenge
        challenge['problems'].sort(key=lambda e: e['props'].get('difficulty', 0))
        challenge_score = 0
        challenge_done = 0
        if self.request.user.is_authenticated():
            submissions = (Submission.objects
                           .filter(user=self.request.user, challenge=challenge_name)
                           .select_related('codes')
                           .annotate(code_count=Count('codes')))
            submissions = {sub.problem: sub for sub in submissions}
            for problem in challenge['problems']:
                submission = submissions.get(problem['name'])
                problem['submission'] = submission
                if submission:
                    challenge_score += submission.score()
                    if submission.succeeded():
                        challenge_done += 1
        for problem in challenge['problems']:
            problem['percentage_level'] = int(problem['props'].get('difficulty', 0) / settings.PROLOGIN_MAX_LEVEL_DIFFICULTY * 100)
        if not challenge.get('display_website', True):
            raise Http404()
        context['challenge_score'] = challenge_score
        context['challenge_done'] = challenge_done == len(challenge['problems'])
        return context


class LegacyChallengeRedirect(RedirectView):
    mapping = {
        'qcm': QUALIFICATION_TUP.code,
        'demi': REGIONAL_TUP.code,
    }

    def get_redirect_url(self, *args, **kwargs):
        event_type = LegacyChallengeRedirect.mapping[self.kwargs['type']]
        return reverse('training:challenge', kwargs={'type': event_type, 'year': self.kwargs['year']})
