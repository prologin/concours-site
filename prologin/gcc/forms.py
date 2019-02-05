import json

from datetime import date

from django import forms

from gcc.models import Answer, Applicant, ApplicantStatusTypes, EventWish, Question, Form, AnswerTypes, Event, Edition


class EmailForm(forms.Form):
    # See here for why 254 max
    # http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690
    email = forms.EmailField(label='Adresse électronique', max_length=254)


def build_dynamic_form(form, user, edition):
    """
    Initialize a django form with fields described in models.Question
    :type form: models.Form
    :type user: settings.AUTH_USER_MODEL
    :type edition: models.Edition
    """

    class DynamicForm(forms.Form):
        """
        A form generated for a specific set of questions, specificly for one
        user.

        `form` and `user` are the parameters of function
        gcc.models.build_dynamic_form(form) which generated this class.
        """

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
                fieldId = 'field' + str(question.pk)

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

        def save(self):
            """
            Saves all filled fields for the applicant defined by the user and
            edition specified in __init__.
            """
            data = self.cleaned_data
            applicant = Applicant.for_user_and_edition(user, self.edition)

            for question in self.questions:
                fieldId = 'field' + str(question.pk)

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
    """
    Select the top three events a candidate wants to participate in.
    """

    priority1 = forms.TypedChoiceField(label='1er choix', required=True)
    priority2 = forms.TypedChoiceField(label='2nd choix', required=False)
    priority3 = forms.TypedChoiceField(label='3e choix', required=False)

    def __init__(self, edition, *args, **kwargs):
        super(ApplicationValidationForm, self).__init__(*args, **kwargs)

        # Get a list of (primary_key, event name) for the selectors
        events = Event.objects.filter(
            signup_start__lt = date.today(),
            signup_end__gt = date.today(),
            edition = edition)
        events_selection = \
            [(None, '')] + [(event.pk, str(event)) for event in events]

        self.fields['priority1'].choices = events_selection
        self.fields['priority2'].choices = events_selection
        self.fields['priority3'].choices = events_selection

    def save(self, user, edition):
        """
        Saves the new applications.
        If an application was already pending for current year, it will be
        replaced. If an application was rejected or accepted, it will raise
        an Application.AlreadyLocked exception.
        """
        data = self.cleaned_data
        applicant = Applicant.for_user_and_edition(user, edition)
        event_wishes = EventWish.objects.filter(applicant=applicant)

        # Verify that no application is already accepted or rejected
        if applicant.status != ApplicantStatusTypes.pending.value:
            raise Applicant.AlreadyLocked(
                'The user has a processed application')

        # Remove previous choices
        event_wishes.delete()

        # Collect selected events, remove duplicatas
        events = [ Event.objects.get(pk=data['priority1']) ]

        if data['priority2'] and data['priority2'] != data['priority1']:
            events.append(Event.objects.get(pk=data['priority2']))

        if data['priority3'] and data['priority3'] not in [data['priority1'], data['priority2']]:
            events.append(Event.objects.get(pk=data['priority3']))

        # Save applications
        for i in range(len(events)):
            event_wish = EventWish(
                applicant = applicant,
                event = events[i],
                order = i + 1)
            event_wish.save()

