from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch, Count, Sum, Case, When, Value, IntegerField
from django.utils.translation import ugettext_lazy as _
from ordered_model.models import OrderedModel

import contest.models
import sponsor.models


def contestant_qcm_consistency_check(contestant, qcm):
    if contestant.edition != qcm.event.edition:
        raise ValidationError("Consistency error: contestant edition ({cont}) and QCM edition ({qcm}) are different"
                              .format(cont=contestant.edition, qcm=qcm.event.edition))


class QcmManager(models.Manager):
    def get_queryset(self):
        return (super().get_queryset()
                .select_related('event', 'event__edition')
                .annotate(question_count=Count('questions', distinct=True),
                          proposition_count=Count('questions__propositions', distinct=True),
                          answer_count=Count('questions__propositions__answers', distinct=True)))


class Qcm(models.Model):
    event = models.ForeignKey(contest.models.Event, related_name='qcms')

    objects = QcmManager()

    def is_completed_for(self, contestant):
        return contestant.qcm_answers.filter(proposition__question__qcm=self).count() == self.question_count

    def score_for_contestant(self, contestant):
        contestant_qcm_consistency_check(contestant, self)
        return Answer.objects.filter(
            contestant=contestant,
            proposition__question__qcm=self,
            proposition__is_correct=True,
        ).count()

    def __str__(self):
        return "QCM for {event} ({count} questions)".format(
            event=self.event,
            count=self.question_count,
        )


class QuestionManager(models.Manager):
    def get_queryset(self):
        return (super().get_queryset()
                .select_related('qcm', 'qcm__event', 'qcm__event__edition')
                .prefetch_related(
                                  Prefetch('propositions',
                                           queryset=Proposition.objects.filter(is_correct=True),
                                           to_attr='correct_propositions'))
                .annotate(proposition_count=Count('propositions'),
                          correct_proposition_count=Sum(Case(When(propositions__is_correct=True, then=Value(1)),
                                                             output_field=IntegerField()))))


class Question(OrderedModel):
    qcm = models.ForeignKey(Qcm, related_name='questions')

    body = models.TextField(verbose_name=_("Question body"))
    verbose = models.TextField(blank=True, verbose_name=_("Verbose description"))
    for_sponsor = models.ForeignKey(sponsor.models.Sponsor, blank=True, null=True, related_name='qcm_questions')

    objects = QuestionManager()

    class Meta(OrderedModel.Meta):
        pass

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

    class Meta:
        unique_together = ('contestant', 'proposition',)

    def clean(self):
        super().clean()
        contestant_qcm_consistency_check(self.contestant, self.proposition.question.qcm)

    @property
    def is_correct(self):
        return self.proposition.is_correct

    def __str__(self):
        return "{contestant} {correct} answers {answer}".format(
            contestant=self.contestant,
            correct="correctly" if self.is_correct else "incorrectly",
            answer=self.proposition,
        )
