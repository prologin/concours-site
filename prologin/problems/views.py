from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.http import Http404, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.views.generic import TemplateView, ListView, DetailView, CreateView, View
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import ModelFormMixin
from rules.contrib.views import PermissionRequiredMixin
import celery
import celery.exceptions
import logging
import time
import requests

from contest.models import Event, Contestant
from problems.forms import SearchForm, CodeSubmissionForm
from problems.tasks import submit_problem_code
from prologin.languages import Language
from prologin.utils import cached
from prologin.utils.scoring import decorate_with_rank
from prologin.views import ChoiceGetAttrsMixin

import problems.models

logger = logging.getLogger(__name__)


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
        if not request.user.has_perm('problems.view_challenge', challenge):
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
        if not request.user.has_perm('problems.view_problem', problem):
            raise ObjectDoesNotExist()
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
                                 if self.request.user.has_perm('problems.view_challenge', c)]
        context['search_form'] = SearchForm()
        if not self.request.user.is_authenticated():
            del context['search_form'].fields['solved']
        return context


class Challenge(PermissionRequiredMixin, TemplateView):
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
    permission_required = 'problems.view_challenge'

    def get_permission_object(self):
        year, event_type, challenge = get_challenge(self.request, self.kwargs)
        return challenge

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year, event_type, challenge = get_challenge(self.request, self.kwargs)
        challenge_score = 0
        challenge_done = 0

        context['challenge'] = challenge
        context['problems'] = challenge.problems

        if challenge.event_type is Event.Type.semifinal and settings.PROLOGIN_SEMIFINAL_MODE:
            # special case because has_perm('problems.view_problem') is heavy
            contestant = Contestant.objects.get(user=self.request.user, edition__year=challenge.year)
            available_problems = contestant.available_semifinal_problems
            for problem in context['problems']:
                if problem not in available_problems:
                    problem.locked = True
        else:
            for problem in context['problems']:
                if not self.request.user.has_perm('problems.view_problem', problem):
                    problem.locked = True

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


class Problem(PermissionRequiredMixin, CreateView):
    """
    Displays a single problem with its statement, its constraints, its samples
    and if the user is authenticated, the code editor and her previous submissions.
    """
    form_class = CodeSubmissionForm
    model = problems.models.SubmissionCode
    template_name = 'problems/problem.html'

    def get_permission_required(self):
        if self.request.method == 'GET':
            return ['problems.view_problem']
        else:
            return ['problems.create_problem_code_submission']

    def get_permission_object(self):
        year, event_type, challenge, problem = get_problem(self.request, self.kwargs)
        return problem

    def get_success_url(self):
        kwargs = self.kwargs.copy()
        kwargs['submission'] = self.submission_code.pk
        return reverse('problems:submission', kwargs=kwargs)

    def get_user_for_submission(self):
        as_user = self.request.GET.get('as')
        if as_user and self.request.user.has_perm('problems.view_others_submissions'):
            return get_object_or_404(get_user_model(), pk=as_user)
        if self.request.user.is_authenticated():
            return self.request.user

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
        user_for_submission = self.get_user_for_submission()
        if user_for_submission:
            user_submission = (user_for_submission.training_submissions
                               .prefetch_related('codes', 'submission_choices')
                               .filter(challenge=challenge.name, problem=problem.name)
                               .first())
        context['user_submission'] = user_submission

        # load forked submission if wanted, and if everything is fine (right user)
        # staff users can fork (thus see) everyone's submissions
        prefill_submission = None
        try:
            prefill_submission = (problems.models.SubmissionCode.objects
                                  .select_related('submission', 'submission__user')
                                  .filter(pk=int(self.request.GET['fork']),
                                          submission__problem=problem.name,
                                          submission__challenge=challenge.name)
                                  .first())
            if prefill_submission is not None and not self.request.user.has_perm('problems.view_code_submission', prefill_submission):
                prefill_submission = None
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
        self.submission_code.save()

        # FIXME: according to the challenge type (qualif, semifinals) we need to
        # do something different here:
        #  - check (if training or qualif)
        #  - check and unlock (if semifinals)

        if self.submission_code.correctable():
            time.sleep(0.3)  # seems to be enough in most cases
            for retry in range(3):
                # schedule correction
                self.submission_code.celery_task_id = celery.uuid()
                self.submission_code.save()
                logger.info("Scheduling code correction (retry %d) for CodeSubmission: %s, task uid: %s",
                            retry, self.submission_code.pk, self.submission_code.celery_task_id)
                future = submit_problem_code.apply_async(args=[self.submission_code.pk],
                                                         task_id=self.submission_code.celery_task_id)
                try:
                    # wait a bit for the result
                    future.get(timeout=settings.PROBLEMS_RESULT_TIMEOUT)
                except celery.exceptions.TimeoutError:
                    pass
                except:
                    delay = 0.3 * (1 + retry)
                    logger.warning("future.get() threw, trying again in %.2f", delay)
                    future.revoke()
                    future.forget()
                    time.sleep(delay)
                    continue
                break

        # we don't use super() because CreateView.form_valid() calls form.save() which overrides
        # the code submission, even if it is modified by the correction task!
        return super(ModelFormMixin, self).form_valid(form)


class SubmissionCode(PermissionRequiredMixin, DetailView):
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
    permission_required = 'problems.view_code_submission'

    def get_queryset(self):
        return (super().get_queryset()
                .select_related('submission', 'submission__user'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, event_type, challenge, problem = get_problem(self.request, self.kwargs)
        context['challenge'] = challenge
        context['problem'] = problem
        return context


class SearchProblems(ChoiceGetAttrsMixin, ListView):
    """
    Searches for problems and display them in a paginated listing.
    """
    context_object_name = 'problems'
    template_name = 'problems/search_results.html'
    paginate_by = 20
    allow_empty = True

    get_attrs = {'sort': ('title', 'year', 'difficulty'),
                 'order': ('asc', 'desc')}

    def get(self, request, *args, **kwargs):
        self.form = SearchForm(self.request.GET if self.request.GET else None)
        if not self.request.user.is_authenticated:
            del self.form.fields['solved']
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        all_results = []
        filter = Q()
        if self.form.is_valid():
            query = slugify(self.form.cleaned_data['query'])
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
                if not self.request.user.has_perm('problems.view_challenge', challenge):
                    continue
                if event_type and challenge.event_type.name != event_type:
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
                    if not query or query in slugify(problem.title):
                        if not self.request.user.has_perm('problems.view_problem', problem):
                            continue
                        filter |= Q(challenge=challenge.name, problem=problem.name)
                        all_results.append(problem)

        if self.request.user.is_authenticated():
            # To display user score on each problem
            submissions = get_user_submissions(self.request.user,
                                               extra_filters=filter)
            submissions = {(sub.challenge, sub.problem): sub for sub in submissions}
            for problem in all_results:
                problem.submission = submissions.get((problem.challenge.name, problem.name))

        sort_by = self.get_clean_attr('sort')
        sort_order = self.get_clean_attr('order')

        o_title = lambda p: p.title.lower()
        o_diff = lambda p: p.difficulty
        o_year = lambda p: p.challenge.year

        key = lambda p: (o_title(p), o_year(p), o_diff(p))
        if sort_by == 'year':
            key = lambda p: (o_year(p), o_title(p), o_diff(p))
        elif sort_by == 'difficulty':
            key = lambda p: (o_diff(p), o_title(p), o_year(p))
        all_results.sort(key=key, reverse=sort_order == 'desc')
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        def get_versions():
            logger.info("Retrieving fresh VM compilers versions")
            return requests.get(settings.PROLOGIN_VM_VERSION_PATH).json()

        cached_versions = {}
        try:
            cached_versions = cached(get_versions, 'problems:compilers:versions')
        except Exception:
            logger.exception("Retrieving fresh VM compilers versions failed")

        languages = [
            (Language.ada, "gcc-ada", "gcc-ada"),
            (Language.brainfuck, "esotope-bfc", "esotope-bfc"),
            (Language.c, "gcc", "GCC"),
            (Language.cpp, "gcc", "G++"),
            (Language.csharp, "mono", "Mono"),
            (Language.fsharp, "fsharp", "Mono"),
            (Language.haskell, "ghc", "GHC"),
            (Language.java, "jdk7-openjdk", "OpenJDK Runtime Environment (IcedTea)"),
            (Language.js, "nodejs", "NodeJS"),
            (Language.lua, "luajit", "LuaJit"),
            (Language.ocaml, "ocaml", "The Objective Caml toplevel"),
            (Language.pascal, "fpc", "Free Pascal compiler"),
            (Language.perl, "perl", "Perl"),
            (Language.php, "php", "PHP"),
            (Language.python2, "python2", "CPython"),
            (Language.python3, "python", "CPython"),
            (Language.scheme, "gambit-c", "Gambit-C"),
            (Language.vb, "mono-basic", "Mono Basic"),
        ]
        context['versions'] = [(lang, description, cached_versions.get(key))
                               for lang, key, description in languages]
        return context


class ChallengeScoreboard(ListView):
    template_name = 'problems/challenge-scoreboard.html'
    allow_empty = True
    context_object_name = 'contestant_scores'
    row_count = 50

    def get(self, request, *args, **kwargs):
        self.year, self.event_type, self.challenge = get_challenge(
                self.request, self.kwargs)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        def score_getter(item):
            return item['total_score']

        def decorator(item, rank, ex_aequo):
            item['rank'] = rank
            item['ex_aequo'] = ex_aequo

        items = (problems.models.Submission.objects
                 .filter(challenge=self.challenge.name, score_base__gt=0,
                         user__is_staff=0)
                 .values('user_id', 'user__username')
                 .annotate(total_score=Sum(problems.models.Submission.ScoreFunc))
                 .order_by('-total_score'))

        decorate_with_rank(items, score_getter, decorator)
        return items[:self.row_count]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['challenge'] = self.challenge
        context['row_count'] = self.row_count
        return context
