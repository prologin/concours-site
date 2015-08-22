from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from contest.models import Event
import contest.models
import problems.models
import prologin.languages



class SearchForm(forms.Form):
    query = forms.CharField(required=False,
                            widget=forms.TextInput(attrs={'placeholder': _("Problem name (optional)")}),
                            label=_("Query"))
    event_type = forms.ChoiceField(choices=[('', _("Any event type")),
                                            (Event.Type.qualification.name, Event.Type.label_for(Event.Type.qualification)),
                                            (Event.Type.semifinal.name, Event.Type.label_for(Event.Type.semifinal))],
                                   required=False,
                                   label=_("Event type"))
    difficulty_min = forms.IntegerField(min_value=0, max_value=settings.PROLOGIN_MAX_LEVEL_DIFFICULTY,
                                        initial=0,
                                        required=False,
                                        label=_("Minimum difficulty"))
    difficulty_max = forms.IntegerField(min_value=0, max_value=settings.PROLOGIN_MAX_LEVEL_DIFFICULTY,
                                        initial=settings.PROLOGIN_MAX_LEVEL_DIFFICULTY,
                                        required=False,
                                        label=_("Maximum difficulty"))

    def clean_query(self):
        return self.cleaned_data['query'].lower().strip()

    def clean(self):
        cd = self.cleaned_data
        if cd['difficulty_min'] is not None and cd['difficulty_max'] is not None and cd['difficulty_min'] > cd['difficulty_max']:
            cd['difficulty_min'], cd['difficulty_max'] = cd['difficulty_max'], cd['difficulty_min']
        return cd


class ProblemWidget(forms.MultiWidget):
    def __init__(self):
        # Code, language
        widgets = [forms.Textarea(), forms.Select()]
        super().__init__(widgets=widgets)

    def decompress(self, value):
        if value is None:
            return []
        return [value.code, value.language]


class ProblemField(forms.MultiValueField):
    widget = ProblemWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.CharField(),
            forms.ChoiceField(choices=prologin.languages.Language.choices())
        )
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        return data_list


class ProblemsForm(forms.ModelForm):
    class Meta:
        model = contest.models.Event
        fields = ()

    def __init__(self, *args, **kwargs):
        self.contestant = kwargs.pop('contestant', None)
        super().__init__(*args, **kwargs)

        problem_list = problems.models.Challenge.objects.filter(event=self.instance)
        if self.contestant:
            answers = {a.challenge.pk: a
                       for a in problems.models.Answer.objects.prefetch_related('challenge')
                                                      .filter(contestant=self.contestant,
                                                              challenge__event=self.instance)}

        for problem in problem_list:
            field_key = 'problem_%d' % problem.pk
            field = self.fields[field_key] = ProblemField()
            field.problem = problem
            if self.contestant:
                field.initial = answers.get(problem.pk)

    def save(self, commit=True):
        return self.instance


class CodeSubmissionForm(forms.ModelForm):
    sourcefile = forms.FileField(required=False)

    class Meta:
        model = problems.models.SubmissionCode
        fields = ('language', 'code', 'summary', 'sourcefile')

    def clean(self):
        if self.cleaned_data['sourcefile']:
            # FIXME: DoS hazard, uploaded sourcefile might be huge
            self.cleaned_data['code'] = self.cleaned_data['sourcefile'].read()
            self.cleaned_data['sourcefile'] = None
        return self.cleaned_data
