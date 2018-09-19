from django import forms

from gcc.models import Question, Forms, ResponseTypes


class EmailForm(forms.Form):
    # See here for why 254 max
    # http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690
    email = forms.EmailField(label='Adresse électronique', max_length=254)


# TODO: cache this function
def build_dynamic_form(form):
    """
    Initialize a django form with fields described in models.Question
    :param form: the form that must be displayed / edited
    :type form: models.Form
    """

    class DynamicForm(forms.Form):
        """
        A form generated for a specific set of questions.
        """
        def __init__(self, *args, **kwargs):
            """
            Initialize a django form with field described as models.Question
            for the form `form` where `form` is the parameter of function
            gcc.models.build_dynamic_form(form) which generated this class.
            """
            super().__init__(*args, **kwargs)

            questions = Question.objects.filter(form=form.value)

            for question in questions:
                # set basic fields parameters
                basic_args = {
                    'label': question.question,
                    'required': question.required,
                }

                if question.response_type == ResponseTypes.boolean.value:
                    self.fields[question.pk] = forms.BooleanField(**basic_args)
                elif question.response_type == ResponseTypes.integer.value:
                    self.fields[question.pk] = forms.IntegerField(**basic_args)
                elif question.response_type == ResponseTypes.date.value:
                    self.fields[question.pk] = forms.DateField(**basic_args)
                elif question.response_type == ResponseTypes.string.value:
                    self.fields[question.pk] = forms.CharField(**basic_args)
                elif question.response_type == ResponseTypes.text.value:
                    self.fields[question.pk] = forms.CharField(
                        widget=forms.Textarea, **basic_args
                    )

    return DynamicForm
