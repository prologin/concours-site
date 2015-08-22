from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import collections
import datetime

from prologin.languages import Language
from prologin.models import CodingLanguageField
from problems.models.problem import Challenge, Problem


SubmissionResults = collections.namedtuple('SubmissionResults', 'correction performance')
SubmissionResult = collections.namedtuple('SubmissionResult', 'name success expected returned')


class Submission(models.Model):
    challenge = models.CharField(max_length=64, db_index=True)
    problem = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='training_submissions')
    score_base = models.IntegerField(default=0)
    malus = models.IntegerField(default=0)

    def latest_submission(self):
        return self.codes.latest()

    def score(self):
        return self.score_base - self.malus

    def challenge_model(self):
        return Challenge.by_low_level_name(self.challenge)

    def problem_model(self):
        return Problem(self.challenge_model(), self.problem)

    def succeeded(self):
        return self.score_base > 0

    def __str__(self):
        return "{}/{} by {}".format(self.challenge, self.problem, self.user)

    class Meta:
        verbose_name = _("Submission")
        verbose_name_plural = _("Submissions")
        unique_together = ('challenge', 'problem', 'user')


class SubmissionCode(models.Model):
    submission = models.ForeignKey(Submission, related_name='codes')
    language = CodingLanguageField()
    code = models.TextField()
    summary = models.TextField(blank=True)
    score = models.IntegerField(null=True, blank=True)
    exec_time = models.IntegerField(null=True, blank=True)
    exec_memory = models.IntegerField(null=True, blank=True)
    date_submitted = models.DateTimeField(default=timezone.now)
    celery_task_id = models.CharField(max_length=128, blank=True)

    def done(self):
        return self.score is not None

    def succeeded(self):
        return self.done() and self.score > 0

    def language_def(self):
        return Language[self.language].value

    def status(self):
        return (_("Pending") if self.score is None
                else _("Failed") if self.score == 0
                else _("Corrected"))

    def expired_result_datetime(self):
        return self.date_submitted + datetime.timedelta(seconds=settings.CELERY_TASK_RESULT_EXPIRES)

    def expired_result(self):
        if not self.celery_task_id:
            # not a chance!
            return True
        # submission is older that Celery task time-to-live
        return self.expired_result_datetime() < timezone.now()

    def correction_results(self):
        if not self.celery_task_id:
            return None
        from problems.tasks import submit_problem_code
        results = submit_problem_code.AsyncResult(self.celery_task_id).result
        if results is None:
            return None
        results = results[1]
        results_corr = []
        results_perf = []
        for result in results:
            if result.get('hidden'):
                continue
            result_obj = SubmissionResult(name=result['id'],
                                          success=result['passed'],
                                          expected=result.get('ref', ''),
                                          returned=result.get('program', ''))
            (results_perf if result['performance'] else results_corr).append(result_obj)
        return SubmissionResults(correction=results_corr, performance=results_perf)

    def __str__(self):
        return "{} in {} (score: {})".format(self.submission,
                                             self.language_def().name,
                                             self.score if self.succeeded() else self.status())

    class Meta:
        verbose_name = _("Submission code")
        verbose_name_plural = _("Submission codes")
        get_latest_by = 'date_submitted'
        ordering = ('-' + get_latest_by, '-pk')


class SubmissionCodeChoice(models.Model):
    submission = models.ForeignKey(Submission, related_name='submission_choices')
    code = models.ForeignKey(SubmissionCode, related_name='submission_code_choices')

    class Meta:
        unique_together = [('submission', 'code')]
