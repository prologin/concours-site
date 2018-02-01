import pprint
from typing import List, Optional

from django.conf import settings
from django.db import models
from django.db.models import F
from django.db.models.functions import Coalesce, Greatest
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from problems.models.problem import Challenge, Problem, TestType, Test
from prologin.languages import Language
from prologin.models import CodingLanguageField
from prologin.utils.db import MsgpackField
from prologin.utils.rec_truncate import rec_truncate


class Result:
    class MetaMixin:
        STATUS = {}

        def __init__(self, data: dict):
            self.data = data

        @property
        def status(self):
            return self.data['meta']['status']

        @property
        def exit_code(self):
            return self.data['meta']['exitcode']

        @property
        def exit_signal(self):
            return self.data['meta']['exitsig']

        @property
        def stdout(self):
            return force_text(self.data['stdout'], strings_only=False, errors='replace').strip()

        @property
        def stderr(self):
            return force_text(self.data['stderr'], strings_only=False, errors='replace').strip()

        @property
        def success(self):
            return self.status == 'OK'

        @property
        def time(self):
            return self.data['meta']['time']

        @property
        def time_wall(self):
            return self.data['meta']['wall-time']

        @property
        def memory(self):
            # in bytes, hence * 1000
            return self.data['meta']['max-rss'] * 1000

        @property
        def human_status(self):
            return self.STATUS[self.status] % {'code': self.exit_code,
                                               'signal': self.exit_signal or _("unknown")}

    class Compilation(MetaMixin):
        STATUS = {
            'OK': _("Compilation went fine."),
            'RUNTIME_ERROR': _("Compilation exited with code %(code)s."),
            'TIMED_OUT': _("Compilation timed out."),
            'SIGNALED': _("Compilation was killed with signal %(signal)s."),
            'INTERNAL_ERROR': _("Compilation crashed with an internal error."),
        }

    class SkippedTest:
        skipped = True

    class Test(MetaMixin):
        STATUS = {
            'OK': _("your program executed fine, but:"),
            'RUNTIME_ERROR': _("your program exited with code %(code)s."),
            'TIMED_OUT': _("you program timed out."),
            'SIGNALED': _("your program was killed with signal %(signal)s."),
            'INTERNAL_ERROR': _("your program crashed with an internal error."),
        }
        skipped = False

        def __init__(self, reference: Test, data: dict, test_passes: bool):
            super().__init__(data)
            self.reference = reference
            self.test_passes = test_passes

        @property
        def expected_stdout(self):
            return self.reference.stdout

        @property
        def hidden(self):
            return self.reference.hidden

        @property
        def success(self):
            return super().success and self.test_passes

        @classmethod
        def parse(cls, problem: Problem, tests: list):
            from problems.camisole import test_passes
            correction = []
            performance = []
            skipped = False
            references = problem.tests
            ref_dict = {ref.name: ref for ref in references}
            test_dict = {test['name']: test for test in tests if test}

            for ref in references:
                is_corr = ref.type is TestType.correction
                storage = (correction if is_corr else performance)
                test = test_dict.get(ref.name)

                if not test or skipped:
                    storage.append(Result.SkippedTest())
                    continue

                test_ok = test_passes(ref_dict[test['name']], test)
                storage.append(Result.Test(data=test, reference=ref, test_passes=test_ok))
                if not test_ok and problem.stop_early:
                    skipped = True

            return correction, performance

    def __init__(self, compilation: Optional[Compilation], correction: List[Test], performance: List[Test]):
        self.compilation = compilation
        self.correction = correction
        self.performance = performance

    @classmethod
    def parse(cls, problem: Problem, data: dict):
        compilation = None
        correction = []
        performance = []
        if 'compile' in data:
            compilation = Result.Compilation(data['compile'])
        if not compilation or compilation.success:
            correction, performance = Result.Test.parse(problem, data.get('tests', []))
        return cls(compilation, correction, performance)


class Submission(ExportModelOperationsMixin('submission'), models.Model):
    challenge = models.CharField(max_length=64, db_index=True)
    problem = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='training_submissions', on_delete=models.CASCADE)
    score_base = models.IntegerField(default=0)
    malus = models.IntegerField(default=0)

    def challenge_model(self) -> Challenge:
        return Challenge.by_low_level_name(self.challenge)

    def problem_model(self) -> Problem:
        return Problem(self.challenge_model(), self.problem)

    def latest_submission(self):
        return self.codes.latest()

    def first_code_success(self):
        return self.codes.filter(score__gt=0).earliest()

    def score(self):
        return max(0, self.score_base - self.malus)

    def succeeded(self):
        return self.score_base > 0

    def has_malus(self):
        return self.malus > 0

    def __str__(self):
        return "{}/{} by {}".format(self.challenge, self.problem, self.user)

    class Meta:
        verbose_name = _("Submission")
        verbose_name_plural = _("Submissions")
        unique_together = ('challenge', 'problem', 'user')

    def get_score_func(prefix=None):
        p = prefix + '__' if prefix is not None else ''
        return Greatest(Coalesce(F(p + 'score_base') - F(p + 'malus'), 0), 0)

    # Use like this: queryset.annotate(score=ScoreFunc)
    ScoreFunc = get_score_func()


class SubmissionCode(ExportModelOperationsMixin('submission_code'), models.Model):
    submission = models.ForeignKey(Submission, related_name='codes', on_delete=models.CASCADE)
    language = CodingLanguageField()
    code = models.TextField()
    summary = models.TextField(blank=True)
    score = models.IntegerField(null=True, blank=True)
    date_submitted = models.DateTimeField(default=timezone.now)
    date_corrected = models.DateTimeField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=128, blank=True)
    result = MsgpackField(null=True, blank=True)

    def done(self):
        return not self.correctable() or self.score is not None

    def succeeded(self):
        return self.done() and self.score is not None and self.score > 0

    def language_enum(self) -> Language:
        return Language[self.language]

    def correctable(self):
        return self.language_enum().correctable()

    def has_result(self):
        if not self.correctable():
            return False
        if not self.done():
            return False
        if not self.celery_task_id or not self.date_corrected:
            return False
        return self.result is not None

    def status(self):
        return _("Pending") if not self.done() else _("Corrected")

    def correction_results(self):
        if not self.celery_task_id or not self.date_corrected:
            return None
        if self.result is None:
            return None
        return Result.parse(self.submission.problem_model(), self.result)

    def request_printable(self):
        req = self.generate_request()
        req = rec_truncate(req, maxlen=100)
        return pprint.pformat(req, width=72)

    def result_printable(self):
        rep = rec_truncate(self.result, maxlen=100)
        return pprint.pformat(rep, width=72)

    def get_absolute_url(self):
        problem = self.submission.problem_model()
        return reverse('problems:submission', kwargs={
            'year': problem.challenge.year,
            'type': problem.challenge.event_type.name,
            'problem': problem.name, 'submission': self.id,
        })

    def generate_request(self) -> dict:
        """Generate a camisole request for the SubmissionCode."""
        problem = self.submission.problem_model()

        def build_tests():
            for ref in problem.tests:
                yield {'name': ref.name, 'stdin': ref.stdin}

        language = self.language_enum()
        request = {
            'lang': language.value.camisole_name,
            'source': self.code,
            'all_fatal': True,
            'execute': problem.execution_limits(language),
            # FIXME: this is arbitrary
            'compile': {'cg-mem': int(1e7),
                        'time': 20,
                        'wall-time': 60,
                        'fsize': 4000},
            'tests': list(build_tests()),
        }
        return request

    def __str__(self):
        return "{} in {} (score: {})".format(self.submission,
                                             self.language_enum().name_display(),
                                             self.score if self.succeeded() else self.status())

    class Meta:
        verbose_name = _("Submission code")
        verbose_name_plural = _("Submission codes")
        get_latest_by = 'date_submitted'
        ordering = ('-' + get_latest_by, '-pk')


class SubmissionCodeChoice(ExportModelOperationsMixin('submission_code_choice'), models.Model):
    submission = models.ForeignKey(Submission, related_name='submission_choices', on_delete=models.CASCADE)
    code = models.ForeignKey(SubmissionCode, related_name='submission_code_choices', on_delete=models.CASCADE)

    class Meta:
        unique_together = [('submission', 'code')]


class ExplicitProblemUnlock(models.Model):
    challenge = models.CharField(max_length=64, db_index=True)
    problem = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='explicit_problem_unlocks',
                             on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
                                   related_name='explicit_problem_unlocks_created')
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "{}/{} for {}".format(self.challenge, self.problem, self.user.username)

    class Meta:
        verbose_name = _("Explicit problem unlock")
        verbose_name_plural = _("Explicit problem unlocks")
        unique_together = [('challenge', 'problem', 'user')]
