from django import forms
from django.utils.translation import ugettext_lazy as _
import random

import qcm.models


class RandomOrderingModelChoiceField(forms.ModelChoiceField):
    """
    Implementation of ModelChoiceField that shuffle the field choices according
    to the seed given as kwarg `ordering_seed`, so the ordering is kept
    consistent between requests.
    """
    def __init__(self, *args, **kwargs):
        self.ordering_seed = kwargs.pop('ordering_seed')
        super().__init__(*args, **kwargs)

        choices = list(self.choices)
        if self.empty_label is not None:
            # empty label is always the first item
            empty_label = choices.pop(0)
        # save state
        state = random.getstate()
        # apply our own seed
        random.seed(self.ordering_seed)
        random.shuffle(choices)
        if self.empty_label is not None:
            choices.append(empty_label)
        # restore state
        random.setstate(state)
        self.choices = choices


class QcmForm(forms.ModelForm):
    class Meta:
        model = qcm.models.Qcm
        fields = ()

    def __init__(self, *args, **kwargs):
        self.contestant = kwargs.pop('contestant', None)
        self.readonly = kwargs.pop('readonly', False)
        ordering_seed = kwargs.pop('ordering_seed')
        super().__init__(*args, **kwargs)
        if self.contestant:
            answers = {e.proposition.question.pk: e.proposition
                       for e in qcm.models.Answer.objects.prefetch_related('proposition', 'proposition__question')
                                                 .filter(contestant=self.contestant, proposition__question__qcm=self.instance)}
        for question in self.instance.questions.prefetch_related('propositions').all():
            field_key = 'qcm_q_%d' % question.pk
            field = self.fields[field_key] = RandomOrderingModelChoiceField(
                required=False,
                queryset=question.propositions.all(),
                widget=forms.RadioSelect,
                empty_label=_("I don't know"),
                ordering_seed=ordering_seed,
            )
            if self.readonly:
                field.widget.attrs['disabled'] = 'disabled'
            field.question = question
            if self.contestant:
                field.initial = answers.get(question.pk)

    def save(self, commit=True):
        instance = self.instance
        # delete previous answers
        self.contestant.qcm_answers.filter(proposition__question__qcm=instance).delete()
        answers = []
        for proposition in self.cleaned_data.values():
            if proposition is not None:
                answers.append(qcm.models.Answer(contestant=self.contestant, proposition=proposition))
        qcm.models.Answer.objects.bulk_create(answers)
        return instance
