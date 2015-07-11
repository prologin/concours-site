from django.views.generic import TemplateView, RedirectView
from django.http import Http404
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
        try:
            event_type = Event.Type[self.kwargs['type']]
        except KeyError:
            raise Http404()
        try:
            context['challenge'] = challenge = problems.models.Challenge.by_year_and_event_type(year, event_type)
            if not challenge.displayable:
                raise ObjectDoesNotExist
        except ObjectDoesNotExist:
            raise Http404()

        context['problems'] = sorted(challenge.problems, key=lambda p: p.difficulty)

        challenge_score = 0
        challenge_done = 0

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


class Problem(TemplateView):
    template_name = 'problems/problem.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = context['year'] = int(self.kwargs['year'])
        try:
            event_type = Event.Type[self.kwargs['type']]
        except KeyError:
            raise Http404()
        try:
            context['challenge'] = challenge = problems.models.Challenge.by_year_and_event_type(year, event_type)
            if not challenge.displayable:
                raise ObjectDoesNotExist
            context['problem'] = problem = problems.models.Problem(challenge, self.kwargs['problem'])
            tackled_by = list(problems.models.Submission.objects.filter(challenge=challenge.name,
                                                                        problem=problem.name))
            context['meta_tackled_by'] = len(tackled_by)
            # Could also be written tackled_by.filter(score__gt=0).count() but
            # 1. would do two queries 2. would fail if succeeded() impl changes
            context['meta_solved_by'] = sum(1 for sub in tackled_by if sub.succeeded())
        except ObjectDoesNotExist:
            raise Http404()
        return context


class SearchProblems(TemplateView):
    template_name = 'problems/search_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = form = SearchForm(self.request.GET if self.request.GET else None)
        all_results = []
        if form.is_valid():
            query = form.cleaned_data['query']
            event_type = form.cleaned_data['event_type']
            difficulty_min = form.cleaned_data['difficulty_min']
            difficulty_max = form.cleaned_data['difficulty_max']
            for challenge in problems.models.Challenge.all():
                if not challenge.displayable:
                    continue
                if event_type and challenge.event_type.name == event_type:
                    continue
                for problem in challenge.problems:
                    if difficulty_min and problem.difficulty < difficulty_min:
                        continue
                    if difficulty_max and problem.difficulty > difficulty_max:
                        continue
                    if not query or query in problem.title.lower():
                        all_results.append(problem)

        all_results.sort(key=lambda p: p.title)
        paginator = Paginator(all_results, 15)
        page = self.request.GET.get('page')
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        context['page_obj'] = page_obj
        context['problem_count'] = len(all_results)
        return context


class LegacyChallengeRedirect(RedirectView):
    permanent = False
    legacy_mapping = {
        'qcm': Event.Type.qualification,
        'demi': Event.Type.semifinal,
    }

    def parse(self):
        return self.kwargs['year'], LegacyChallengeRedirect.legacy_mapping[self.kwargs['type']].name

    def get_redirect_url(self, *args, **kwargs):
        year, event_type = self.parse()
        return reverse('training:challenge', kwargs={'year': year,
                                                     'type': event_type})


class LegacyProblemRedirect(LegacyChallengeRedirect):
    def get_redirect_url(self, *args, **kwargs):
        year, event_type = super().parse()
        return reverse('training:problem', kwargs={'year': year,
                                                   'type': event_type,
                                                   'problem': self.kwargs['problem']})
