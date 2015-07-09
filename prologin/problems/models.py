from django.db import models
from django.conf import settings
from ordered_model.models import OrderedModel

from contest.models import Event
from problems.problem import get_problem
from prologin.languages import Language
from prologin.models import CodingLanguageField



class Submission(models.Model):
    challenge = models.CharField(max_length=64, db_index=True)
    problem = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='problem_submissions')
    score_base = models.IntegerField(default=0)
    malus = models.IntegerField(default=0)

    def latest_submission(self):
        return self.codes.latest()

    def score(self):
        return self.score_base - self.malus

    def problem_specification(self, **kwargs):
        return get_problem(self.challenge, self.problem, **kwargs)

    def succeeded(self):
        return self.score_base > 0

    def __str__(self):
        return "{}/{} by {}".format(self.challenge, self.problem, self.user)

    class Meta:
        unique_together = ('challenge', 'problem', 'user')


class SubmissionCode(models.Model):
    submission = models.ForeignKey(Submission, related_name='codes')
    language = CodingLanguageField()
    code = models.TextField()
    score = models.IntegerField(null=True)
    exec_time = models.IntegerField(null=True)
    exec_memory = models.IntegerField(null=True)
    date_submitted = models.DateTimeField(auto_now_add=True)

    def done(self):
        return self.score is not None

    def succeeded(self):
        return self.done() and self.score > 0

    def language_def(self):
        return Language[self.language].value

    def __str__(self):
        return "{} in {} (score: {})".format(self.submission,
                                             self.language_def().name,
                                             self.score if self.succeeded() else
                                             "failed" if self.done() else
                                             "pending")

    class Meta:
        get_latest_by = 'date_submitted'
        ordering = ('-' + get_latest_by,)
