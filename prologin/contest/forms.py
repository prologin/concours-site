from betterforms.multiform import MultiModelForm
from collections import OrderedDict
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from contest.widgets import EventWishChoiceField
import contest.models


class ContestantUserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'address', 'postal_code', 'city',
                  'country', 'phone', 'school_stage')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    epita = forms.BooleanField(required=True, initial=False,
            label=_("I am not a student at EPITA or EPITECH."))

    def __init__(self, *args, **kwargs):
        kwargs.pop('edition')
        complete = kwargs.pop('complete')
        super().__init__(*args, **kwargs)
        self.fields['last_name'].help_text = _("We need your real name and address for legal reasons, as the Prologin "
                                               "staff engages its responsibility to supervise you during the regional "
                                               "events and the finale.")
        if self.instance:
            url = reverse('users:profile', args=[self.instance.pk])
            self.fields[self.Meta.fields[-1]].help_text = ('<i class="fa fa-info-circle"></i> ' +
                                                           _('You can modify or review all your personal information '
                                                             'on your <a href="%(url)s">profile page</a>.')
                                                           % {'url': url})
        for field_name in ('first_name', 'last_name', 'address', 'postal_code',
                           'city', 'country'):
            self.fields[field_name].required = True
        if complete:
            self.fields['epita'].initial = True

    def clean_epita(self):
        data = self.cleaned_data['epita']
        if not data:
            raise forms.ValidationError(_("You cannot participate if you are an "
                    "EPITA/EPITECH student"))
        return data


class ContestantForm(forms.ModelForm):
    class Meta:
        model = contest.models.Contestant
        fields = ('shirt_size', 'preferred_language', 'event_wishes')

    def __init__(self, *args, **kwargs):
        edition = kwargs.pop('edition')
        kwargs.pop('complete')
        super().__init__(*args, **kwargs)
        # Overwrite event_wishes with our custom over-engineered field
        self.fields['event_wishes'] = EventWishChoiceField(
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
            # FIXME: figure why we have to do the ordering manually
            self.initial['event_wishes'] = list(self.instance.event_wishes
                                                .order_by('eventwish__order')
                                                .values_list('pk', flat=True))
        self._edition = edition


class CombinedContestantUserForm(MultiModelForm):
    form_classes = OrderedDict([
        ('user', ContestantUserForm),
        ('contestant', ContestantForm),
    ])
