from django import forms
from django.utils.translation import ugettext_lazy as _
from problems import QUALIFICATION_TUP, REGIONAL_TUP
import contest.models
import problems.models
import prologin.languages


class SearchForm(forms.Form):
    query = forms.CharField(required=False,
                            widget=forms.TextInput(attrs={'placeholder': _("Problem name (optional)")}))
    event_type = forms.ChoiceField(choices=[('', _("Any event type")),
                                            (QUALIFICATION_TUP.code, QUALIFICATION_TUP.display_name),
                                            (REGIONAL_TUP.code, REGIONAL_TUP.display_name)],
                                   required=False)
    difficulty = forms.ChoiceField(choices=[(str(i), i) for i in range(1, 6)],
                                   widget=forms.CheckboxSelectMultiple(),
                                   label=_("Difficulty"))


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