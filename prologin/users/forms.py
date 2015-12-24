from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from captcha.fields import ReCaptchaField

from prologin.models import Gender
from .widgets import PreviewFileInput


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'gender', 'birthday',
                  'address', 'postal_code', 'city', 'country',
                  'phone', 'email', 'allow_mailing',
                  'preferred_language', 'school_stage', 'timezone',
                  'preferred_locale', 'avatar', 'picture',)
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
            ("", _("Other or prefer not to tell")),
        ]
        if not self.instance.team_memberships.count():
            # If not part of any team, makes no sense to add a staff picture
            self.fields.pop('picture', None)


class RegisterForm(forms.ModelForm):
    captcha = ReCaptchaField(label="",
                             help_text='<small>{}</small>'.format(
                                 _("Please check the box above and complete the additional tasks if any. "
                                   "This is required to fight spamming bots on the website.")))

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password', 'allow_mailing', 'captcha')
        widgets = {
            'password': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254, required=True,
                             widget=forms.EmailInput(attrs={'placeholder': _("Your email address")}))


class ProloginAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _("Username or email")
        self.fields['username'].help_text = _("This field is case insensitive. It means capitals and small letters are "
                                              "considered to be equal.")
        self.error_messages['invalid_login'] = _("Please enter a correct username (or email) and password.")
