from django import forms
from django.conf import settings

import contest.models


class OrderedModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, *args, order_field='order', min_count=0, max_count=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_count = min_count
        self.max_count = max_count
        self.order_field = order_field

    def _check_values(self, value):
        pass

class ContestantForm(forms.ModelForm):

    class Meta:
        model = contest.models.Contestant
        fields = ('shirt_size', 'preferred_language', 'event_wishes')

    def __init__(self, *args, **kwargs):
        edition = kwargs.pop('edition')
        super().__init__(*args, **kwargs)
        self.fields['event_wishes'].queryset = (self.fields['event_wishes'].queryset
                                                .filter(edition=edition,
                                                        type=contest.models.Event.Type.semifinal.value))
        self._edition = edition

    def clean_event_wishes(self):
        return self.cleaned_data['event_wishes'][:settings.PROLOGIN_SEMIFINAL_MAX_WISH_COUNT]
