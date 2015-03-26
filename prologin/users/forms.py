from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from .widgets import PreviewFileInput


class UserSimpleForm(forms.ModelForm):
    class Meta:
        # TODO: add preferred_locale with a language dropdown
        model = get_user_model()
        fields = ('first_name', 'last_name', 'gender', 'email',
                  'address', 'postal_code', 'city', 'country',
                  'phone', 'birthday', 'preferred_language',
                  'newsletter', 'allow_mailing', 'avatar', 'picture')
        widgets = {
            'avatar': PreviewFileInput(),
            'picture': PreviewFileInput(),
        }

    def clean(self):
        if not self.cleaned_data['allow_mailing']:
            # This is also done client side in JS
            self.cleaned_data['newsletter'] = False
        return self.cleaned_data


class RegisterForm(forms.ModelForm):
    captcha = CaptchaField(help_text=_("Type the four letters to prove you are not an automated bot."))
    newsletter = forms.BooleanField(required=False, label=_("Subscribe to the newsletter"))

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password', 'newsletter', 'captcha')
        widgets = {
            'password': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
