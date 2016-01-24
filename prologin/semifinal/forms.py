from django import forms
from django.utils.translation import ugettext_lazy as _

import contest.models
import problems.models


class ExplicitProblemUnlockForm(forms.Form):
    problem = forms.ChoiceField(label=_("Problem"))
    contestants = forms.ModelMultipleChoiceField(queryset=(contest.models.Contestant.objects
                                                           .select_related('user')
                                                           .filter(user__is_staff=False, user__is_superuser=False)),
                                                 label=_("Contestants"),
                                                 help_text=_("You can select all contestants using Ctrl-A."))

    @staticmethod
    def contestant_label(contestant):
        user = contestant.user
        return "{} ({})".format(user.username, user.get_full_name())

    @staticmethod
    def problem_label(problem):
        return "[{}] {}".format(problem.difficulty, problem.title)

    def __init__(self, *args, **kwargs):
        challenge = kwargs.pop('challenge')
        assert isinstance(challenge, problems.models.Challenge)

        super().__init__(*args, **kwargs)

        self.fields['problem'].choices = [(problem.name, ExplicitProblemUnlockForm.problem_label(problem))
                                          for problem in challenge.problems]

        self.fields['contestants'].queryset = (self.fields['contestants'].queryset
                                               .filter(edition=challenge.year))
        self.fields['contestants'].label_from_instance = ExplicitProblemUnlockForm.contestant_label
