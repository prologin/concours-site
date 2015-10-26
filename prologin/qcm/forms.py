from django import forms
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
import random

from prologin.templatetags.markup import markdown
import qcm.models


class RadioChoiceInputWithInstance(forms.widgets.RadioChoiceInput):
    """
    So we can access the instance underlying this choice in the template.
    """
    def __init__(self, name, value, attrs, instance, index):
        if isinstance(instance, (tuple, list)):
            self.instance = None
            choice = instance
        else:
            self.instance = instance
            choice = (instance.pk, markdown(force_text(instance)))
        super().__init__(name, value, attrs, choice, index)


class PropositionRadioFieldRenderer(forms.widgets.RadioFieldRenderer):
    choice_input_class = RadioChoiceInputWithInstance


class PropositionRadioSelect(forms.widgets.RadioSelect):
    renderer = PropositionRadioFieldRenderer


class RandomOrderingModelChoiceField(forms.ModelChoiceField):
    """
    Implementation of ModelChoiceField that shuffle the field choices according
    to the seed given as kwarg `ordering_seed`, so the ordering is kept
    consistent between requests.
    """
    def __init__(self, *args, **kwargs):
        self.ordering_seed = kwargs.pop('ordering_seed')
        super().__init__(*args, **kwargs)

        choices = list(self.queryset)
        # save state
        state = random.getstate()
        # apply our own seed
        random.seed(self.ordering_seed)
        random.shuffle(choices)
        if self.empty_label is not None:
            choices.append(('', self.empty_label))
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
            answers = {e.proposition.question.pk: e.textual_answer if e.proposition.question.is_open_ended else e.proposition
                       for e in
                       qcm.models.Answer.objects.prefetch_related('proposition', 'proposition__question')
                                                 .filter(contestant=self.contestant, proposition__question__qcm=self.instance)}
        # The form is either text box (open ended question) or a list of
        # choices (otherwise).
        for question in self.instance.questions.prefetch_related('propositions').all():
            field_key = 'qcm_q_%d' % question.pk
            if question.is_open_ended:
                textinput = forms.TextInput(attrs={'class': 'form-control'})  # For bootstrap css
                field = self.fields[field_key] = forms.CharField(widget=textinput)
            else:
                field = self.fields[field_key] = RandomOrderingModelChoiceField(
                    required=False,
                    queryset=question.propositions.all(),
                    widget=PropositionRadioSelect,
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
        for field_key, proposition in self.cleaned_data.items():
            if proposition is not None:
                # field key is 'qcm_q_ID' where ID is the primary key
                question_pk = int(field_key.split('_')[-1])
                question_obj = qcm.models.Question.objects.get(pk=question_pk)
                # TODO(halfr): handle non openeded questions
                proposition_obj = question_obj.propositions.all()[0]
                answers.append(qcm.models.Answer(contestant=self.contestant,
                    proposition=proposition_obj, textual_answer=proposition))
        qcm.models.Answer.objects.bulk_create(answers)
        return instance
