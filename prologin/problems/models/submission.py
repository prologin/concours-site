import collections
import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from prologin.languages import Language
from prologin.models import CodingLanguageField
from problems.models.problem import Challenge, Problem

SubmissionResults = collections.namedtuple('SubmissionResults', 'compilation correction performance')
SubmissionTest = collections.namedtuple('SubmissionTest', 'name success expected returned debug hidden')


class Submission(ExportModelOperationsMixin('submission'), models.Model):
    challenge = models.CharField(max_length=64, db_index=True)
    problem = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='training_submissions')
    score_base = models.IntegerField(default=0)
    malus = models.IntegerField(default=0)

    def latest_submission(self):
        return self.codes.latest()

    def score(self):
        return max(0, self.score_base - self.malus)

    def challenge_model(self) -> Challenge:
        return Challenge.by_low_level_name(self.challenge)

    def problem_model(self) -> Problem:
        return Problem(self.challenge_model(), self.problem)

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


class SubmissionCode(ExportModelOperationsMixin('submission_code'), models.Model):
    submission = models.ForeignKey(Submission, related_name='codes')
    language = CodingLanguageField()
    code = models.TextField()
    summary = models.TextField(blank=True)
    score = models.IntegerField(null=True, blank=True)
    exec_time = models.IntegerField(null=True, blank=True)
    exec_memory = models.IntegerField(null=True, blank=True)
    date_submitted = models.DateTimeField(default=timezone.now)
    date_corrected = models.DateTimeField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=128, blank=True)

    def done(self):
        return self.score is not None

    def succeeded(self):
        return self.done() and self.score > 0

    def language_enum(self):
        return Language[self.language]

    def correctable(self):
        return self.language_enum().correctable()

    def status(self):
        return (_("Expired") if self.expired_result() and not self.done()
                else _("Pending") if not self.done()
                else _("Corrected"))

    def expired_result_datetime(self):
        if not self.date_corrected:
            return None
        return self.date_corrected + datetime.timedelta(seconds=settings.CELERY_TASK_RESULT_EXPIRES)

    def expired_result(self):
        expired_datetime = self.expired_result_datetime()
        if not expired_datetime:
            return False
        # submission is older that Celery task time-to-live
        return expired_datetime < timezone.now()

    def correction_results(self):
        if not self.celery_task_id or not self.date_corrected:
            return None
        from problems.tasks import submit_problem_code
        results = submit_problem_code.AsyncResult(self.celery_task_id).result
        if results is None:
            return None
        compilation, tests = results
        test_corr = []
        test_perf = []
        for test in tests:
            result_obj = SubmissionTest(name=test['id'],
                                        success=test['passed'],
                                        expected=test.get('ref', '') or '',
                                        returned=test.get('program', '') or '',
                                        hidden=test.get('hidden'),
                                        debug=test.get('debug', '') or '')
            (test_perf if test['performance'] else test_corr).append(result_obj)
        return SubmissionResults(compilation=compilation, correction=test_corr, performance=test_perf)

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
    submission = models.ForeignKey(Submission, related_name='submission_choices')
    code = models.ForeignKey(SubmissionCode, related_name='submission_code_choices')

    class Meta:
        unique_together = [('submission', 'code')]
