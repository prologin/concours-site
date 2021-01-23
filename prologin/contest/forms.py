from collections import OrderedDict

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from django.urls import reverse
from django.forms.models import ModelChoiceIterator
from django.utils import formats
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

import contest.models
import schools.models
from contest.widgets import EventWishChoiceField
from prologin import utils
from prologin.models import Gender
from prologin.utils.forms import NewableModelChoiceField
from prologin.utils.multiforms import MultiModelForm


class SchoolField(NewableModelChoiceField):
    def create_new(self, model, value, exc):
        new_prefix = '_new_'
        fb_prefix = 'fb_'
        if not value.startswith(new_prefix):
            raise exc
        __, school = value.split(new_prefix, 1)
        if school.startswith(fb_prefix):
            # Facebook suggestion
            __, fbid = school.split(fb_prefix, 1)
            fb_school = schools.models.Facebook.get(fbid)
            if fb_school:
                school = fb_school['name']
        school = school.strip()
        # check if by chance it already exists
        try:
            school, created = model.objects.get_or_create(name__iexact=school, defaults={'name': school})
            if created:
                school.save()
        except MultipleObjectsReturned:
            school = schools.models.School.objects.filter(name__iexact=school).first()
        return school

    def label_from_instance(self, obj):
        return obj.name


class ContestantUserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'birthday', 'address', 'postal_code', 'city',
                  'country', 'phone', 'gender', 'school_stage')
        optional_fields = ('phone', 'gender', 'school_stage')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'gender': forms.RadioSelect(),
        }

    epita = forms.BooleanField(required=True, initial=True,
                               label=mark_safe(_("I am <strong>not</strong> a student at EPITA.")))

    def __init__(self, *args, **kwargs):
        kwargs.pop('edition')
        kwargs.pop('complete')
        super().__init__(*args, **kwargs)
        self.fields['gender'].label = _("How do you prefer to be described?")
        self.fields['gender'].choices = [
            (Gender.female.value, mark_safe(_("<em>She is writing code for the contest</em>"))),
            (Gender.male.value, mark_safe(_("<em>He is writing code for the contest</em>"))),
            ("", _("Other or prefer not to tell")),
        ]
        # Assigning the help_text there because for some reason reverse_lazy() is not lazy enough in
        # the static field declaration above
        self.fields['epita'].help_text = _('Students from EPITA are <a href="%(url)s">not allowed</a> '
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
        for field in self.Meta.optional_fields:
            self.fields[field].help_text = _("Optional.")

    def clean_epita(self):
        data = self.cleaned_data['epita']
        if not data:
            raise forms.ValidationError(_("You cannot participate if you are an "
                    "EPITA student"))
        return data


class ContestantForm(forms.ModelForm):
    class Meta:
        model = contest.models.Contestant
        fields = (
            'shirt_size', 'preferred_language',
            'assignation_semifinal_wishes', 'school',
            'learn_about_contest'
            )
        optional_fields = ('learn_about_contest')
        field_classes = {'school': SchoolField}
        labels = {'school': _("Your school")}

    def __init__(self, *args, **kwargs):
        edition = kwargs.pop('edition')
        kwargs.pop('complete')
        super().__init__(*args, **kwargs)

        # Overwrite assignation_semifinal_wishes with our custom over-engineered field
        self.fields['assignation_semifinal_wishes'] = EventWishChoiceField(
            queryset=(contest.models.Event.objects
                      .select_related('center')
                      .filter(edition=edition, type=contest.models.Event.Type.semifinal.value)),
            min_choices=0,
            max_choices=settings.PROLOGIN_SEMIFINAL_MAX_WISH_COUNT,
            label=_("Regional event center wishes"),
            help_text=_("This is where you would like to seat the regional events if you "
                        "are selected. Choose at least one and up to three wishes, in "
                        "order of preference. Most of the time, we are able to satisfy "
                        "your first choice."))
        if self.instance:
            # BEGIN fucking hack not to display full queryset
            school_field = self.fields['school']
            it = ModelChoiceIterator(school_field)
            if self.instance.school:
                it.queryset = it.queryset.filter(pk=self.instance.school.pk)
            else:
                it.queryset = it.queryset.none()
            school_field.choices = list(it)
            # END fucking hack
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

class ContestantSemifinalEventForm(forms.Form):

    def __init__(self, *args, **kwargs):
        possible_events = kwargs.pop('possible_events')
        super().__init__(*args, **kwargs)
        self.fields['selected_event'] = forms.ChoiceField(choices=possible_events, required=True, label=_('Selected event'))
