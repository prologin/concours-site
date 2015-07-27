from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from captcha.fields import ReCaptchaField

from prologin.models import Gender
from .widgets import PreviewFileInput


class UserProfileForm(forms.ModelForm):
    class Meta:
        # TODO: add preferred_locale with a language dropdown
        model = get_user_model()
        fields = ('first_name', 'last_name', 'gender', 'birthday',
                  'address', 'postal_code', 'city', 'country',
                  'phone', 'email', 'allow_mailing', 'newsletter',
                  'preferred_language', 'avatar', 'picture',)
        widgets = {
            'avatar': PreviewFileInput(),
            'picture': PreviewFileInput(),
            'gender': forms.RadioSelect(),
            'address': forms.Textarea(attrs=dict(rows=2)),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gender'].required = False
        self.fields['gender'].label = _("How do you prefer to be described?")
        self.fields['gender'].choices = [
            (Gender.female.value, mark_safe(_("<em>She is writing code for the contest</em>"))),
            (Gender.male.value, mark_safe(_("<em>He is writing code for the contest</em>"))),
            ("", _("I prefer not to say")),
        ]
        if not self.instance.team_memberships.count():
            # If not part of any team, makes no sense to add a staff picture
            self.fields.pop('picture', None)

    def clean(self):
        if not self.cleaned_data['allow_mailing']:
            # This is also done client side in JS
            self.cleaned_data['newsletter'] = False
        return self.cleaned_data


class RegisterForm(forms.ModelForm):
    captcha = ReCaptchaField(label="",
                             help_text='<small>{}</small>'.format(
                                 _("Please check the box above and complete the additional tasks if any. "
                                   "This is required to fight spamming bots on the website.")))
    newsletter = forms.BooleanField(required=False, label=_("Subscribe to the newsletter"),
                                    help_text='<small>{}</small>'.format(
                                        _("We do not send more than a few mails each year! We use that to "
                                          "notice you when new editions begin and when results are available.")))

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password', 'newsletter', 'captcha')
        widgets = {
            'password': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254, required=True,
                             widget=forms.EmailInput(attrs={'placeholder': _("Your email address")}))
