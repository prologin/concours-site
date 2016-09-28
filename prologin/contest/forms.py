from betterforms.multiform import MultiModelForm
from collections import OrderedDict
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import formats
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from contest.widgets import EventWishChoiceField
import contest.models
from prologin import utils


class ContestantUserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'birthday', 'address', 'postal_code', 'city',
                  'country', 'phone', 'school_stage')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    epita = forms.BooleanField(required=True, initial=False,
                               label=mark_safe(_("I am <strong>not</strong> a student at EPITA or EPITECH.")))

    def __init__(self, *args, **kwargs):
        kwargs.pop('edition')
        complete = kwargs.pop('complete')
        super().__init__(*args, **kwargs)
        # Assigning the help_text there because for some reason reverse_lazy() is not lazy enough in
        # the static field declaration above
        self.fields['epita'].help_text = _('Students from EPITA and EPITCH are <a href="%(url)s">not allowed</a> '
                                           'to join the contest.') % {'url': reverse('pages:about-qualification') + '#no-epita'}
        self.fields['last_name'].help_text = _("We need your real name and address for legal reasons, as the Prologin "
                                               "staff engages its responsibility to supervise you during the regional "
                                               "events and the finale.")
        self.fields['country'].help_text = _("We will send the invitation to the regional events at this address, so "
                                             "make sure it's valid.")
        self.fields['birthday'].help_text = _("Format: %(format)s") % {'format': utils.translate_format(formats.get_format('DATE_INPUT_FORMATS')[0])}
        if self.instance:
            url = reverse('users:profile', args=[self.instance.pk])
            self.fields[self.Meta.fields[-1]].help_text = ('<i class="fa fa-info-circle"></i> ' +
                                                           _('You can modify or review all your personal information '
                                                             'on your <a href="%(url)s">profile page</a>.')
                                                           % {'url': url})
        for field_name in ('first_name', 'last_name', 'address', 'postal_code',
                           'city', 'country', 'birthday'):
            self.fields[field_name].required = True
        if complete:
            self.fields['epita'].initial = True

    def clean_epita(self):
        data = self.cleaned_data['epita']
        if not data:
            raise forms.ValidationError(_("You cannot participate if you are an "
                    "EPITA/EPITECH student"))
        return data

    def clean_birthday(self):
        data = self.cleaned_data['birthday']
        birth_year = settings.PROLOGIN_EDITION - settings.PROLOGIN_MAX_AGE
        if data.year < birth_year:
            raise forms.ValidationError(_("You cannot participate if you are "
                "born before {}").format(birth_year))
        return data


class ContestantForm(forms.ModelForm):
    class Meta:
        model = contest.models.Contestant
        fields = ('shirt_size', 'preferred_language', 'assignation_semifinal_wishes')

    def __init__(self, *args, **kwargs):
        edition = kwargs.pop('edition')
        kwargs.pop('complete')
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].required = True
        # Overwrite assignation_semifinal_wishes with our custom over-engineered field
        self.fields['assignation_semifinal_wishes'] = EventWishChoiceField(
            queryset=(contest.models.Event.objects
                      .select_related('center')
                      .filter(edition=edition, type=contest.models.Event.Type.semifinal.value)),
            min_choices=settings.PROLOGIN_SEMIFINAL_MIN_WISH_COUNT,
            max_choices=settings.PROLOGIN_SEMIFINAL_MAX_WISH_COUNT,
            label=_("Regional event center wishes"),
            help_text=_("This is where you would like to seat the regional events if you "
                        "are selected. Choose at least one and up to three wishes, in "
                        "order of preference. Most of the time, we are able to satisfy "
                        "your first choice."))
        if self.instance:
            # FIXME: figure why we have to do the ordering manually
            self.initial['assignation_semifinal_wishes'] = list(self.instance.assignation_semifinal_wishes
                                                                .order_by('eventwish__order')
                                                                .values_list('pk', flat=True))
        self._edition = edition


class CombinedContestantUserForm(MultiModelForm):
    form_classes = OrderedDict([
        ('user', ContestantUserForm),
        ('contestant', ContestantForm),
    ])
