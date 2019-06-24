# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from crispy_forms import layout
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm as DjangoAuthenticationForm
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from captcha.fields import ReCaptchaField

from prologin.models import Gender
from prologin.utils import _
from prologin.utils.forms import ConfirmDangerMixin
from .widgets import PreviewFileInput

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    readonly_during_contest = ('first_name', 'last_name', 'address', 'birthday',
                               'postal_code', 'city', 'country',)

    class Meta:
        model = User
        # Take care when changing this: update the indexes in __init__ accordingly
        fields = (
            # left column
            'first_name', 'last_name', 'email', 'birthday',
            'address', 'postal_code', 'city', 'country',
            'phone', 'school_stage',
            # right column
            'gender', 'allow_mailing', 'timezone',
            'preferred_locale', 'avatar', 'picture',)
        widgets = {
            'avatar': PreviewFileInput(image_attrs={'style': 'max-width: 90px; max-height: 90px;'}),
            'picture': PreviewFileInput(image_attrs={'style': 'max-width: 90px; max-height: 90px;'}),
            'gender': forms.RadioSelect(),
            'address': forms.Textarea(attrs=dict(rows=2)),
        }

    def __init__(self, *args, **kwargs):
        self.can_edit_profile = kwargs.pop('can_edit_profile', True)
        super().__init__(*args, **kwargs)

        self.fields['gender'].required = False
        self.fields['gender'].label = _("How do you prefer to be described?")

        self.homes = []
        home_fields = []
        for candidate in self.instance.get_homes():
            home_year = candidate.edition.year
            home_field = forms.BooleanField(
                required=False,
                initial=candidate.is_home_public,
                label=(_("%(year)s final home") % {'year': home_year}),
            )
            self.homes.append(candidate)
            key = 'home_{}'.format(home_year)
            home_fields.append(key)
            self.fields[key] = home_field

        self.fields['gender'].choices = [
            (Gender.female.value, mark_safe(_("<em>She is writing code for the contest</em>"))),
            (Gender.male.value, mark_safe(_("<em>He is writing code for the contest</em>"))),
            ("", _("Other or prefer not to tell")),
        ]
        if not self.can_edit_profile:
            for field in self.readonly_during_contest:
                self.fields[field].widget.attrs['readonly'] = 'readonly'
                self.fields[field].help_text = format_html(
                    '<small class="smaller">{}</small>',
                    _("You can not change your details during the contest. If there is an "
                      "important change you want to make, please contact the staff."))

        if not self.instance.team_memberships.count():
            # If not part of any team, makes no sense to add a staff picture
            self.fields.pop('picture', None)

        self.helper = FormHelper(self)
        self.helper.form_tag = False
        if home_fields:
            # regroup home checkboxes in a panel
            home_panel = layout.Div(
                layout.Div(layout.HTML(format_html('<i class="fa fa-book"></i> {}', _("Public homes"))), css_class="panel-heading"),
                layout.Div(
                    layout.HTML(format_html('<p class="text-muted">{}</p>',
                                            _("Checked editions will make the files available for download to anyone."))),
                    *(layout.Field(f, template='bootstrap3/layout/inline_field.html') for f in home_fields),
                    css_class="panel-body"),
                css_class="panel panel-default")
            self.helper[len(self.helper) - len(home_fields):] = [home_panel]
        # input, input, ...
        self.helper[:10].wrap_together(layout.Div, css_class="col-md-6")
        # COL, input, input...
        self.helper[1:].wrap_together(layout.Div, css_class="col-md-6")
        # COL, COL
        self.helper[:].wrap_together(layout.Div, css_class="row")

    def clean(self):
        for candidate in self.homes:
            candidate.is_home_public = self.cleaned_data['home_{}'.format(candidate.edition.year)]
            candidate.save()

        if not self.can_edit_profile:
            for field in self.readonly_during_contest:
                self.cleaned_data.pop(field, None)
        return super().clean()


class RegisterForm(forms.ModelForm):
    captcha = ReCaptchaField(label="",
                             help_text='<small>{}</small>'.format(
                                 _("Please check the box above and complete the additional tasks if any. "
                                   "This is required to fight spamming bots on the website.")))

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'allow_mailing', 'captcha')
        widgets = {
            'password': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_username(self):
        if User.objects.filter(username__iexact=self.cleaned_data['username']):
            raise forms.ValidationError(_("This username is already in use. "
                                          "Please supply a different username."))
        return self.cleaned_data['username'].strip().lower()

    def clean_email(self):
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(_("This email address is already in use. "
                                          "Please supply a different email address."))
        return self.cleaned_data['email'].strip().lower()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254, required=True,
                             widget=forms.EmailInput(attrs={'placeholder': _("Your email address")}))


class AuthenticationForm(DjangoAuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _("Username or email")
        self.fields['username'].help_text = _("This field is case insensitive. It means capitals and small letters are "
                                              "considered to be equal.")
        self.error_messages['invalid_login'] = _("Please enter a correct username (or email) and password.")


class ConfirmDeleteUserForm(ConfirmDangerMixin, forms.ModelForm):
    username_conf = forms.CharField(
        required=True, label=_("Your username"),
        help_text=_("Type your username to confirm you know what you are doing."))

    class Meta:
        model = get_user_model()
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.instance
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout('username_conf', 'password_conf')
        self.fields['username_conf'].widget.attrs['placeholder'] = self.instance.username
        # https://bugs.chromium.org/p/chromium/issues/detail?id=468153
        self.fields['username_conf'].widget.attrs['autocomplete'] = 'new-username'
        self.fields['password_conf'].widget.attrs['autocomplete'] = 'new-password'
			
    def clean_username_conf(self):
        if self.cleaned_data['username_conf'] != self.instance.username:
            raise forms.ValidationError(_("Wrong username."))
