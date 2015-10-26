from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q, F, Sum
from django.http import Http404, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.views.generic import TemplateView, ListView, DetailView, CreateView, View
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import ModelFormMixin
import celery
import celery.exceptions

from contest.models import Event
from problems.forms import SearchForm, CodeSubmissionForm
from prologin.languages import Language
from problems.tasks import submit_problem_code
import problems.models


def get_challenge(request, kwargs) -> (int, Event.Type, problems.models.Challenge):
    """
    Loads a challenge from URL kwargs.
    """
    year = int(kwargs['year'])
    try:
        event_type = Event.Type[kwargs['type']]
    except KeyError:
        raise Http404()
    try:
        challenge = problems.models.Challenge.by_year_and_event_type(year, event_type)
        if not (challenge.displayable or request.user.is_staff):
            raise ObjectDoesNotExist()
    except ObjectDoesNotExist:
        raise Http404()
    return year, event_type, challenge


def get_problem(request, kwargs) -> (int, Event.Type, problems.models.Challenge, problems.models.Problem):
    """
    Loads a problem (and its challenge) from URL kwargs.
    """
    year, event_type, challenge = get_challenge(request, kwargs)
    try:
        problem = problems.models.Problem(challenge, kwargs['problem'])
    except ObjectDoesNotExist:
        raise Http404()
    return year, event_type, challenge, problem


def get_user_submissions(user, extra_filters=Q()):
    """
    Fetches all submissions for the given user, using extra filters if needed.
    """
    return (problems.models.Submission.objects
                           .filter(user=user)
                           .filter(extra_filters)
                           .prefetch_related('codes'))


class Index(TemplateView):
    """
    Displays a table of challenges grouped by year and the search form.
    """
    template_name = 'problems/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['challenges'] = [c for c in problems.models.Challenge.all()
                if c.displayable or self.request.user.is_staff]
        context['search_form'] = SearchForm()
        if not self.request.user.is_authenticated():
            del context['search_form'].fields['solved']
        return context


class Challenge(TemplateView):
    """
    Displays the challenge statement and the list of all problems within a
    challenge along with the user score, if authenticated.
    """
    template_name = 'problems/challenge.html'
    # Event.Type name → (Event.Type, challenge prefix)
    event_category_mapping = {
        Event.Type.qualification.name: (Event.Type.qualification, 'qcm'),
        Event.Type.semifinal.name: (Event.Type.semifinal, 'demi'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year, event_type, challenge = get_challenge(self.request, self.kwargs)
        challenge_score = 0
        challenge_done = 0

        context['challenge'] = challenge
        context['problems'] = sorted(challenge.problems, key=lambda p: p.difficulty)

        if self.request.user.is_authenticated():
            # To display user score on each problem
            submissions = get_user_submissions(self.request.user,
                                               extra_filters=Q(challenge=challenge.name))
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
    """
    Displays a single problem with its statement, its constraints, its samples
    and if the user is authenticated, the code editor and her previous submissions.
    """
    form_class = CodeSubmissionForm
    model = problems.models.SubmissionCode
    template_name = 'problems/problem.html'

    def get_success_url(self):
        kwargs = self.kwargs.copy()
        kwargs['submission'] = self.submission_code.pk
        return reverse('training:submission', kwargs=kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, event_type, challenge, problem = get_problem(self.request, self.kwargs)

        context['problem'] = problem
        context['languages'] = list(Language)
        context['challenge'] = challenge
        context['templatable_languages'] = list(problem.language_templates.keys())

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

        # load forked submission if wanted, and if everything is fine (right user)
        # staff users can fork (thus see) everyone's submissions
        prefill_submission = None
        try:
            permissions = Q()
            if not self.request.user.is_staff:
                permissions = Q(submission__user=self.request.user)
            prefill_submission = (problems.models.SubmissionCode.objects
                                  .select_related('submission', 'submission__user')
                                  .filter(pk=int(self.request.GET['fork']),
                                          submission__problem=problem.name,
                                          submission__challenge=challenge.name)
                                  .filter(permissions)
                                  .first())
        except (KeyError, ValueError):  # (no "fork=", non-numeric fork id)
            pass
        context['prefill_submission'] = prefill_submission

        return context

    def form_valid(self, form):
        if not self.request.user.is_authenticated():
            return HttpResponseForbidden()
        context = self.get_context_data()
        self.submission_code = form.save(commit=False)
        submission = context['user_submission']
        if not submission:
            # first code submission; create parent submission
            submission = problems.models.Submission(user=self.request.user,
                                                    challenge=context['challenge'].name,
                                                    problem=context['problem'].name)
            submission.save()
        self.submission_code.submission = submission
        if self.submission_code.correctable():
            self.submission_code.celery_task_id = celery.uuid()
        self.submission_code.save()

        # FIXME: according to the challenge type (qualif, semifinals) we need to
        # do something different here:
        #  - check (if training or qualif)
        #  - check and unlock (if semifinals)

        if self.submission_code.correctable():
            # schedule correction
            future = submit_problem_code.apply_async(args=[self.submission_code.pk],
                                                     task_id=self.submission_code.celery_task_id,
                                                     throw=False)
            try:
                # wait a bit for the result
                future.get(timeout=settings.TRAINING_RESULT_TIMEOUT)
            except celery.exceptions.TimeoutError:
                pass
        # we don't use super() because CreateView.form_valid() calls form.save() which overrides
        # the code submission, even if it is modified by the correction task!
        return super(ModelFormMixin, self).form_valid(form)


class SubmissionCode(DetailView):
    """
    Displays a code submission and, if they are still available, the correction & performance results.

    In case the page is rendered before the correction system has finished correcting the program,
    we use Javascript to regularly ask if the correction is done already. If it is, we just reload the
    page.

    The correction & performance results are stored in the Celery backend (typically Redis) and are
    not supposed to be long-lived. Hence the following cases:
        - submission is corrected (score is not empty): we display the results if still available;
        - submission is not yet corrected (score is empty):
            - submission is young enough: we display a "waiting" status and try to fetch the result
              with Javascript;
            - submission is too old to have any result OR it has no Celery task id, eg. if the
              submission was imported from legacy Drupal: we explain that to the user.
    """
    model = problems.models.SubmissionCode
    context_object_name = 'submission'
    pk_url_kwarg = 'submission'
    template_name = 'problems/submission.html'

    def get_queryset(self):
        permissions = Q()
        if not self.request.user.is_staff:
            permissions = Q(submission__user=self.request.user)
        return (super().get_queryset()
                .select_related('submission', 'submission__user')
                .filter(permissions))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, event_type, challenge, problem = get_problem(self.request, self.kwargs)
        context['challenge'] = challenge
        context['problem'] = problem
        return context


class SearchProblems(ListView):
    """
    Searches for problems and display them in a paginated listing.
    """
    context_object_name = 'problems'
    template_name = 'problems/search_results.html'
    paginate_by = 20
    allow_empty = True

    def get(self, request, *args, **kwargs):
        self.form = SearchForm(self.request.GET if self.request.GET else None)
        if not self.request.user.is_authenticated:
            del self.form.fields['solved']
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        all_results = []
        filter = Q()
        if self.form.is_valid():
            query = self.form.cleaned_data['query']
            event_type = self.form.cleaned_data['event_type']
            difficulty_min = self.form.cleaned_data['difficulty_min']
            difficulty_max = self.form.cleaned_data['difficulty_max']
            solved = self.form.cleaned_data['solved']
            solved_problems = set()
            if self.request.user.is_authenticated() and solved:
                solved_problems = set(problems.models.Submission.objects
                                      .filter(user=self.request.user,
                                              score_base__gt=0)
                                      .values_list('challenge', 'problem'))
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
                    if solved and solved_problems:
                        key = (challenge.name, problem.name)
                        if ((solved == 'solved' and key not in solved_problems)
                                or solved == 'unsolved' and key in solved_problems):
                            continue
                    if not query or query in problem.title.lower():
                        filter |= Q(challenge=challenge.name, problem=problem.name)
                        all_results.append(problem)

        if self.request.user.is_authenticated():
            # To display user score on each problem
            submissions = get_user_submissions(self.request.user,
                                               extra_filters=filter)
            submissions = {(sub.challenge, sub.problem): sub for sub in submissions}
            for problem in all_results:
                problem.submission = submissions.get((problem.challenge.name, problem.name))

        all_results.sort(key=lambda p: p.title.lower())
        return all_results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = self.form
        return context


class AjaxSubmissionCorrected(BaseDetailView):
    """
    Ajax endpoint that returns a JSON boolean: true if the given submission is done (i.e. has a score),
    false otherwise.
    This is used in the Submission view, to poll for results when they eventually become available.
    """
    model = problems.models.SubmissionCode
    pk_url_kwarg = 'submission'

    def get_queryset(self):
        return (super().get_queryset().select_related('submission__user')
                .filter(submission__user=self.request.user))

    def render_to_response(self, context):
        has_result = self.object.done()
        return JsonResponse(has_result, safe=False)


class AjaxLanguageTemplate(View):
    """
    Ajax endpoint that returns the code stub for the language template of a problem, for a given language.
    """
    def get(self, request, *args, **kwargs):
        try:
            lang = Language.guess(request.GET['lang'])
            if lang is None:
                raise KeyError
            year, event_type, challenge, problem = get_problem(self.request, kwargs)
            template = problem.language_templates[lang]
            return JsonResponse(template, safe=False)
        except KeyError:
            return HttpResponseBadRequest()


class ManualView(TemplateView):
    template_name = 'problems/manual.html'


class ChallengeScoreboard(ListView):
    template_name = 'problems/challenge-scoreboard.html'
    allow_empty = True
    context_object_name = 'contestant_scores'

    def get(self, request, *args, **kwargs):
        self.year, self.event_type, self.challenge = get_challenge(
                self.request, self.kwargs)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        def wrap_with_ranks(ranking):
            current_rank = 1
            previous_score = None
            for i, line in enumerate(ranking, 1):
                line['ex_aequo'] = True
                line['rank'] = current_rank
                if (previous_score is None
                        or previous_score != line['total_score']):
                    line['rank'] = current_rank
                    line['ex_aequo'] = False
                    previous_score = line['total_score']
                    current_rank = i
                yield line

        return wrap_with_ranks((problems.models.Submission.objects
                .filter(challenge=self.challenge.name, score_base__gt=0)
                .values('user_id', 'user__username')
                .annotate(total_score=Sum(F('score_base') - F('malus')))
                .order_by('-total_score'))[:50])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['challenge'] = self.challenge
        return context
