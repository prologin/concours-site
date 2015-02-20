from django.db import models
from django.utils.translation import ugettext_lazy as _
from ordered_model.models import OrderedModel
import prologin.models
import contest.models


class Qcm(models.Model):
    event = models.ForeignKey(contest.models.Event, related_name='qcms')

    def __str__(self):
        return "QCM for {event} ({count} questions)".format(
            event=self.event,
            count=self.questions.count(),
        )


class Question(OrderedModel):
    qcm = models.ForeignKey(Qcm, related_name='questions')

    body = models.TextField(verbose_name=_("Question body"))
    verbose = models.TextField(blank=True, verbose_name=_("Extra verbose description"))
    for_sponsor = models.ForeignKey(prologin.models.Sponsor, blank=True, null=True, related_name='qcm_questions')

    class Meta(OrderedModel.Meta):
        pass

    @property
    def proposition_count(self):
        return self.propositions.count()

    def correct_propositions(self):
        return self.propositions.filter(is_correct=True)

    @property
    def correct_proposition_count(self):
        return self.propositions.filter(is_correct=True).count()

    def __str__(self):
        return self.body


class Proposition(models.Model):
    question = models.ForeignKey(Question, related_name='propositions')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Answer(models.Model):
    contestant = models.ForeignKey(contest.models.Contestant, related_name='qcm_answers')
    proposition = models.ForeignKey(Proposition, related_name='answers')

    @property
    def is_correct(self):
        return self.proposition.is_correct

    def __str__(self):
        return "{contestant} {correct} answers {answer}".format(
            contestant=self.contestant,
            correct="correctly" if self.is_correct else "incorrectly",
            answer=self.proposition,
        )
