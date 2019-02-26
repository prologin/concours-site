from collections import OrderedDict
from datetime import date
from django import forms
from django.contrib.auth import get_user_model
from django.utils import formats
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

from gcc.models import (Answer, AnswerTypes, Applicant, ApplicantStatusTypes,
                        Event, EventWish)

from prologin import utils
from prologin.utils.multiforms import MultiForm
from prologin.models import Gender

class EmailForm(forms.Form):
    # See here for why 254 max
    # http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690
    email = forms.EmailField(label=_('Email address'), max_length=254)


def build_dynamic_form(form, user, edition):
    """Build a form with fields described in models.Question"""

    class DynamicForm(forms.Form):

        @staticmethod
        def question_field_name(question_id):
            return 'field_{}'.format(question_id)

        def __init__(self, *args, **kwargs):
            kwargs.pop('instance')
            super(DynamicForm, self).__init__(*args, **kwargs)

            self.edition = edition
            self.form = form

            # Add fields to the form
            self.questions = self.form.question_list.all()

            for question in self.questions:
                # set basic fields parameters
                basic_args = {
                    'label': question.question,
                    'required': question.required,
                    'help_text': question.comment
                }
                field_id = self.question_field_name(question.pk)

                # Try to load existing configuration
                try:
                    answer = Answer.objects.get(
                        question=question,
                        applicant__user=user,
                        applicant__edition=edition
                    )
                    basic_args['initial'] = answer.response
                except Answer.DoesNotExist:
                    pass

                if question.response_type == AnswerTypes.boolean.value:
                    self.fields[field_id] = forms.BooleanField(**basic_args)
                elif question.response_type == AnswerTypes.integer.value:
                    self.fields[field_id] = forms.IntegerField(**basic_args)
                elif question.response_type == AnswerTypes.date.value:
                    self.fields[field_id] = forms.DateField(**basic_args)
                elif question.response_type == AnswerTypes.string.value:
                    self.fields[field_id] = forms.CharField(**basic_args)
                elif question.response_type == AnswerTypes.text.value:
                    self.fields[field_id] = forms.CharField(
                        widget=forms.Textarea, **basic_args)
                elif question.response_type == AnswerTypes.multichoice.value:
                    self.fields[field_id] = forms.ChoiceField(
                        choices=[
                            (str(choice), question.meta['choices'][choice])
                            for choice in question.meta['choices'].keys()
                        ], **basic_args)


        def save(self):
            """
            Saves all filled fields for the applicant defined by the user and
            edition specified in __init__.
            """
            data = self.cleaned_data
            applicant = Applicant.for_user_and_edition(user, self.edition)

            for question in self.questions:
                field_id = self.question_field_name(question.pk)

                if data[field_id] is not None:
                    # Try to modify existing answer, create a new answer if it
                    # doesn't exist
                    try:
                        answer = Answer.objects.get(applicant=applicant,
                                                    question=question)
                    except Answer.DoesNotExist:
                        answer = Answer(applicant=applicant, question=question)

                    answer.response = data[field_id]
                    answer.save()

    return DynamicForm

class ApplicantUserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'birthday', 'gender', 'address',
                  'postal_code', 'city', 'country', 'phone', 'school_stage')
        optional_fields = ('phone', 'school_stage')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'gender': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gender'].label = _('How do you identify?')
        self.fields['gender'].help_text = \
            _('You have to identify as a girl/woman to apply to the Girls Can '
              'Code! summer camps.')
        self.fields['gender'].choices = [
            (Gender.female.value,
             mark_safe(_('<em>I identify as girl/woman.</em>'))),
            (Gender.male.value,
             mark_safe(_('<em>I identify as boy/man.</em>'))),
            ("", _("Other or prefer not to tell")),
        ]
        # Assigning the help_text there because for some reason reverse_lazy() is not lazy enough in
        # the static field declaration above
        self.fields['last_name'].help_text = _(
            'We need your real name and address for legal reasons, as the '
            'Prologin staff engages its responsibility to supervise you '
            'during the summer camps.')
        self.fields['country'].help_text = _(
            'We will send the invitation to the summer camps at this address, '
            'so make sure it\'s valid.')
        self.fields['birthday'].help_text = _('Format: %(format)s') % {
            'format': utils.translate_format(formats.get_format('DATE_INPUT_FORMATS')[0])}

        if self.instance:
            url = reverse('gcc:index')
            self.fields[self.Meta.fields[-1]].help_text = (
                '<i class="fa fa-info-circle"></i> {}'.format(_(
                    'You can modify or review all your personal information '
                    'on your <a href="%(url)s">profile page</a>.'
                ) % {'url': url}))
        for field in self.Meta.optional_fields:
            self.fields[field].help_text = _("Optional.")

    def clean_gender(self):
        gender = self.cleaned_data['gender']
        if not gender == Gender.female.value:
            raise forms.ValidationError(_(
                'You cannot participate if you don\'t identify as a '
                'girl/woman.'))
        return gender == Gender.female.value


class CombinedApplicantUserForm(MultiForm):

    def __init__(self, *args, **kwargs):
        self.edition = kwargs.pop('edition')
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def get_form_classes(self):
        form_classes = OrderedDict([
            ('user', ApplicantUserForm),
            ('editionform', build_dynamic_form(self.edition.signup_form,
                                               self.user, self.edition)),
        ])
        return form_classes

    def save(self):
        self.forms['user'].save()
        self.forms['editionform'].save()

class ApplicationWishesForm(forms.Form):
    """Select the top three events a candidate wants to participate in."""

    priority1 = forms.TypedChoiceField(label=_('1st choice'), required=True)
    priority2 = forms.TypedChoiceField(label=_('2nd choice'), required=False)
    priority3 = forms.TypedChoiceField(label=_('3rd choice'), required=False)

    def __init__(self, edition, *args, **kwargs):
        super(ApplicationWishesForm, self).__init__(*args, **kwargs)

        # Get a list of (primary_key, event name) for the selectors
        events = Event.objects.filter(
            signup_start__lt=date.today(),
            signup_end__gt=date.today(),
            edition=edition)
        events_selection = \
            [(None, '')] + [(event.pk, str(event)) for event in events]

        self.fields['priority1'].choices \
            = self.fields['priority2'].choices \
            = self.fields['priority3'].choices \
            = events_selection

    def save(self, user, edition):
        """
        Save the new applications.
        If an application was already being edited for current year, it will
        be replaced. If an application was rejected or accepted, it will raise
        an Application.AlreadyLocked exception.
        """
        data = self.cleaned_data
        applicant = Applicant.for_user_and_edition(user, edition)

        # Verify that no application is already accepted or rejected
        if applicant.status != ApplicantStatusTypes.incomplete.value:
            raise Applicant.AlreadyLocked(
                'The user has a processed application')

        # Remove previous choices
        EventWish.objects.filter(applicant=applicant).delete()

        # Collect selected events, remove duplicates
        events = [Event.objects.get(pk=data['priority1'])]

        if data['priority2'] and data['priority2'] != data['priority1']:
            events.append(Event.objects.get(pk=data['priority2']))

        if data['priority3'] and data['priority3'] not in [data['priority1'], data['priority2']]:
            events.append(Event.objects.get(pk=data['priority3']))

        # Save applications
        for i, event in enumerate(events):
            EventWish(applicant=applicant, event=event, order=i+1).save()
