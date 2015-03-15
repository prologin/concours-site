from django.db import models
from ordered_model.models import OrderedModel
from contest.models import Event, Contestant
from prologin.languages import Language


class Challenge(OrderedModel):
    event = models.ForeignKey(Event, related_name='challenges')
    title = models.CharField(max_length=128)
    problem_ref = models.CharField(max_length=128)
    question = models.TextField()
    comments = models.TextField(blank=True)

    @property
    def edition(self):
        return self.event.edition

    def __str__(self):
        return self.title


class Answer(models.Model):
    challenge = models.ForeignKey(Challenge, related_name='answers')
    contestant = models.ForeignKey(Contestant, related_name='challenge_answers')
    date_submitted = models.DateTimeField(auto_now_add=True)
    is_final = models.BooleanField(default=False)
    language = models.CharField(max_length=16, choices=Language.choices())
    code = models.TextField()

    class Meta:
        ordering = ('-date_submitted',)