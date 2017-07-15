import unicodedata

from adminsortable.models import SortableMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch, Count, Sum, Case, When, Value, IntegerField
from django.utils.translation import ugettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

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


class FullQcmManager(QcmManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related('questions', 'questions__propositions')


class Qcm(ExportModelOperationsMixin('qcm'), models.Model):
    event = models.ForeignKey(contest.models.Event, related_name='qcms')

    objects = QcmManager()
    full_objects = FullQcmManager()

    def completed_question_count_for(self, contestant):
        return contestant.qcm_answers.filter(proposition__question__qcm=self).count()

    def is_completed_for(self, contestant):
        return self.completed_question_count_for(contestant) == self.question_count

    def score_for_contestant(self, contestant):
        contestant_qcm_consistency_check(contestant, self)
        return Answer.objects.filter(
            contestant=contestant,
            proposition__question__qcm=self,
            proposition__is_correct=True,
        ).count()

    def __getattr__(self, item):
        # FIXME: this is so hackish I'm gonna die
        # The idea is: annotations are only added to the instances retrieved by using
        # Qcm.objects.something(), they're obviously not available when accessing the
        # instance by other means (eg. related object). Hence __str__ fails because
        # question_count is not hydrated. So we have to do a new query to retrieve
        # the annotations. Same issue in all other damn models using "complex"
        # annotations in their __str__ that may be called from anywhere.
        if item in ('question_count',):
            return getattr(self.__class__.objects.get(pk=self.pk), item)
        raise AttributeError()

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


class Question(ExportModelOperationsMixin('question'), SortableMixin):
    qcm = models.ForeignKey(Qcm, related_name='questions')

    body = models.TextField(verbose_name=_("Question body"))
    verbose = models.TextField(blank=True, verbose_name=_("Verbose description"))
    for_sponsor = models.ForeignKey(sponsor.models.Sponsor, blank=True, null=True, related_name='qcm_questions')
    order = models.IntegerField(editable=False, db_index=True)
    # Open ended questions have only one correct proposition.
    # The user only sees a text input and has to give his or her answer.
    is_open_ended = models.BooleanField(default=False)

    objects = QuestionManager()

    @property
    def correct_answer(self):
        if self.is_open_ended:
            # shall return one and only one result
            return self.propositions.get(is_correct=True)

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.body


class Proposition(ExportModelOperationsMixin('proposition'), models.Model):
    question = models.ForeignKey(Question, related_name='propositions', verbose_name=_("Question"))
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class AnswerManager(models.Manager):
    def get_queryset(self):
        return (super().get_queryset()
                .select_related('proposition__question__qcm__event__edition', 'contestant__user'))


class Answer(ExportModelOperationsMixin('answer'), models.Model):
    contestant = models.ForeignKey(contest.models.Contestant, related_name='qcm_answers')
    proposition = models.ForeignKey(Proposition, related_name='answers', verbose_name=_("Answer"))
    # Textual answer given by the contestant if the question is open ended.
    textual_answer = models.TextField(blank=True, null=True, verbose_name=_("Textual answer"))

    objects = AnswerManager()

    class Meta:
        unique_together = ('contestant', 'proposition',)

    def clean(self):
        super().clean()
        contestant_qcm_consistency_check(self.contestant, self.proposition.question.qcm)

    @property
    def is_correct(self):
        if self.proposition.question.is_open_ended:
            # Convert unicode to ASCII bytes
            contestant_ascii = unicodedata.normalize('NFKD', self.textual_answer).encode('ASCII', 'ignore')
            answer_ascii = unicodedata.normalize('NFKD', self.proposition.text).encode('ASCII', 'ignore')
            # Normalize harder
            contestant = contestant_ascii.strip().lower()
            answer = answer_ascii.strip().lower()
            return contestant == answer
        else:
            return self.proposition.is_correct

    def __str__(self):
        return "{contestant} {correct} answers {answer}".format(
            contestant=self.contestant,
            correct="correctly" if self.is_correct else "incorrectly",
            answer=self.proposition,
        )
