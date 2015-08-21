from django.views.generic import TemplateView, RedirectView, ListView, CreateView
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

from problems.forms import SearchForm, CodeSubmissionForm
from contest.models import Event
from prologin.languages import Language
import problems.models


def get_challenge(kwargs):
    year = int(kwargs['year'])
    try:
        event_type = Event.Type[kwargs['type']]
    except KeyError:
        raise Http404()
    try:
        challenge = problems.models.Challenge.by_year_and_event_type(year, event_type)
        if not challenge.displayable:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        raise Http404()
    return year, event_type, challenge


def get_user_submissions(user, filter):
    return (problems.models.Submission.objects
                           .filter(user=user)
                           .filter(filter)
                           .prefetch_related('codes'))


class Index(TemplateView):
    template_name = 'problems/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['challenges'] = [c for c in problems.models.Challenge.all() if c.displayable]
        context['search_form'] = SearchForm()
        return context


class Challenge(TemplateView):
    template_name = 'problems/challenge.html'
    # Event.Type name → (Event.Type, challenge prefix)
    event_category_mapping = {
        Event.Type.qualification.name: (Event.Type.qualification, 'qcm'),
        Event.Type.semifinal.name: (Event.Type.semifinal, 'demi'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year, event_type, challenge = get_challenge(self.kwargs)
        challenge_score = 0
        challenge_done = 0

        context['challenge'] = challenge
        context['problems'] = sorted(challenge.problems, key=lambda p: p.difficulty)

        if self.request.user.is_authenticated():
            # To display user score on each problem
            submissions = get_user_submissions(self.request.user,
                                               filter=Q(challenge=challenge.name))
            submissions = {sub.problem: sub for sub in submissions}
            for problem in context['problems']:
                submission = submissions.get(problem.name)
                # Monkey-patch the problem to add the submission object
                if submission:
                    problem.submission = submission
                    challenge_score += submission.score()
                    if submission.succeeded():
                        challenge_done += 1

        context['challenge_score'] = challenge_score
        context['challenge_done'] = challenge_done == len(challenge.problems)

        return context


class Problem(CreateView):
    form_class = CodeSubmissionForm
    model = problems.models.SubmissionCode
    context_object_name = 'submission_form'
    template_name = 'problems/problem.html'

    def get_success_url(self):
        return reverse('training:problem', kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, event_type, challenge = get_challenge(self.kwargs)
        try:
            context['problem'] = problem = problems.models.Problem(challenge, self.kwargs['problem'])
        except ObjectDoesNotExist:
            raise Http404()

        context['languages'] = list(Language)
        context['challenge'] = challenge

        tackled_by = list(problems.models.Submission.objects.filter(challenge=challenge.name,
                                                                    problem=problem.name))
        context['meta_tackled_by'] = len(tackled_by)
        # Could also be written tackled_by.filter(score__gt=0).count() but
        # 1. would do two queries 2. would fail if succeeded() impl changes
        context['meta_solved_by'] = sum(1 for sub in tackled_by if sub.succeeded())

        user_submission = None
        if self.request.user.is_authenticated():
            user_submission = (self.request.user.training_submissions
                               .prefetch_related('codes', 'submission_choices')
                               .filter(challenge=challenge.name, problem=problem.name)
                               .first())
        context['user_submission'] = user_submission
        return context

    def form_valid(self, form):
        if not self.request.user.is_authenticated():
            return HttpResponseForbidden()
        context = self.get_context_data()
        submission_code = form.save(commit=False)
        submission_code.submission = context['user_submission']
        submission_code.save()
        # TODO: schedule correction, wait for a result a few seconds
        # redirect to result if got result, redirect to submission if timeout
        return super().form_valid(form)


class SearchProblems(ListView):
    context_object_name = 'problems'
    template_name = 'problems/search_results.html'
    paginate_by = 20
    allow_empty = True

    def get(self, request, *args, **kwargs):
        self.form = SearchForm(self.request.GET if self.request.GET else None)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        all_results = []
        filter = Q()
        if self.form.is_valid():
            query = self.form.cleaned_data['query']
            event_type = self.form.cleaned_data['event_type']
            difficulty_min = self.form.cleaned_data['difficulty_min']
            difficulty_max = self.form.cleaned_data['difficulty_max']
            for challenge in problems.models.Challenge.all():
                if not challenge.displayable:
                    continue
                if event_type and challenge.event_type.name == event_type:
                    continue
                for problem in challenge.problems:
                    if difficulty_min is not None and problem.difficulty < difficulty_min:
                        continue
                    if difficulty_max is not None and problem.difficulty > difficulty_max:
                        continue
                    if not query or query in problem.title.lower():
                        filter |= Q(challenge=challenge.name, problem=problem.name)
                        all_results.append(problem)

        if self.request.user.is_authenticated():
            # To display user score on each problem
            submissions = get_user_submissions(self.request.user,
                                               filter=filter)
            submissions = {(sub.challenge, sub.problem): sub for sub in submissions}
            for problem in all_results:
                problem.submission = submissions.get((problem.challenge.name, problem.name))

        all_results.sort(key=lambda p: p.title.lower())
        return all_results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = self.form
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
