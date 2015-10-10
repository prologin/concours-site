from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from contest.widgets import EventWishChoiceField
import contest.models


class ContestantForm(forms.ModelForm):
    class Meta:
        model = contest.models.Contestant
        fields = ('shirt_size', 'preferred_language', 'event_wishes')

    def __init__(self, *args, **kwargs):
        edition = kwargs.pop('edition')
        super().__init__(*args, **kwargs)
        # Overwrite event_wishes with our custom over-engineered field
        event_wishes = self.fields['event_wishes'] = EventWishChoiceField(
            queryset=(contest.models.Event.objects
                      .select_related('center')
                      .filter(edition=edition, type=contest.models.Event.Type.semifinal.value)),
            min_choices=settings.PROLOGIN_SEMIFINAL_MIN_WISH_COUNT,
            max_choices=settings.PROLOGIN_SEMIFINAL_MAX_WISH_COUNT,
            label=_("Semifinal center wishes"),
            help_text=_("This is where you would like to seat the regional events if you "
                        "are selected. Choose at least one and up to three wishes, in "
                        "order of preference. Most of the time, we are able to satisfy "
                        "your first choice."))
        if self.instance:
            event_wishes.initial = self.instance.event_wishes
        self._edition = edition
