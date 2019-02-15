import json
from datetime import date
from django import forms
from django.utils.translation import ugettext_lazy as _

from gcc.models import (Answer, AnswerTypes, Applicant, ApplicantStatusTypes,
    Edition, Event, EventWish, Form, Question)


class EmailForm(forms.Form):
    # See here for why 254 max
    # http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690
    email = forms.EmailField(label=_('Email address'), max_length=254)


def build_dynamic_form(form, user, edition):
    """Build a form with fields described in models.Question"""

    class DynamicForm(forms.Form):

        def question_field_name(self, id):
            return 'field_{}'.format(id)

        def __init__(self, *args, **kwargs):
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
                fieldId = self.question_field_name(question.pk)

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
                    self.fields[fieldId] = forms.BooleanField(**basic_args)
                elif question.response_type == AnswerTypes.integer.value:
                    self.fields[fieldId] = forms.IntegerField(**basic_args)
                elif question.response_type == AnswerTypes.date.value:
                    self.fields[fieldId] = forms.DateField(**basic_args)
                elif question.response_type == AnswerTypes.string.value:
                    self.fields[fieldId] = forms.CharField(**basic_args)
                elif question.response_type == AnswerTypes.text.value:
                    self.fields[fieldId] = forms.CharField(
                        widget=forms.Textarea, **basic_args)
                elif question.response_type == AnswerTypes.multichoice.value:
                    self.fields[fieldId] = forms.ChoiceField(
                        choices = [
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
                fieldId = self.question_field_name(question.pk)

                if data[fieldId] is not None:
                    # Try to modify existing answer, create a new answer if it
                    # doesn't exist
                    try:
                        answer = Answer.objects.get(applicant=applicant,
                            question=question)
                    except Answer.DoesNotExist:
                        answer = Answer(applicant=applicant,
                            question=question)

                    answer.response = data[fieldId]
                    answer.save()

    return DynamicForm


class ApplicationValidationForm(forms.Form):
    """Select the top three events a candidate wants to participate in."""

    priority1 = forms.TypedChoiceField(label=_('1st choice'), required=True)
    priority2 = forms.TypedChoiceField(label=_('2nd choice'), required=False)
    priority3 = forms.TypedChoiceField(label=_('3rd choice'), required=False)

    def __init__(self, edition, *args, **kwargs):
        super(ApplicationValidationForm, self).__init__(*args, **kwargs)

        # Get a list of (primary_key, event name) for the selectors
        events = Event.objects.filter(
            signup_start__lt = date.today(),
            signup_end__gt = date.today(),
            edition = edition)
        events_selection = \
            [(None, '')] + [(event.pk, str(event)) for event in events]
        print(events_selection)

        self.fields['priority1'].choices \
            = self.fields['priority2'].choices \
            = self.fields['priority3'].choices \
            = events_selection

    def save(self, user, edition):
        """
        Save the new applications.
        If an application was already pending for current year, it will be
        replaced. If an application was rejected or accepted, it will raise
        an Application.AlreadyLocked exception.
        """
        data = self.cleaned_data
        applicant = Applicant.for_user_and_edition(user, edition)

        # Verify that no application is already accepted or rejected
        if applicant.status != ApplicantStatusTypes.pending.value:
            raise Applicant.AlreadyLocked(
                'The user has a processed application')

        # Remove previous choices
        EventWish.objects.filter(applicant=applicant).delete()

        # Collect selected events, remove duplicates
        events = [ Event.objects.get(pk=data['priority1']) ]

        if data['priority2'] and data['priority2'] != data['priority1']:
            events.append(Event.objects.get(pk=data['priority2']))

        if data['priority3'] and data['priority3'] not in [data['priority1'], data['priority2']]:
            events.append(Event.objects.get(pk=data['priority3']))

        # Save applications
        for i in range(len(events)):
            EventWish(
                applicant = applicant,
                event = events[i],
                order = i + 1
            ).save()
