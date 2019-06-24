# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django import forms
from prologin.utils import _


class NewableModelChoiceField(forms.ModelChoiceField):
    def to_python(self, value):
        try:
            return super().to_python(value)
        except forms.ValidationError as exc:
            return self.create_new(self.queryset.model, value, exc)

    def create_new(self, model, value, exc):
        raise NotImplementedError()


class ConfirmDangerMixin(forms.Form):
    password_conf = forms.CharField(widget=forms.PasswordInput, label=_("Your current password"))

    def __init__(self, *args, **kwargs):
        # the user doing the dangerous operation, who must provide their password
        self.action_user = kwargs.pop('action_user')
        super().__init__(*args, **kwargs)

    def clean_password_conf(self):
        if not self.action_user.check_password(self.cleaned_data['password_conf']):
            raise forms.ValidationError(_("Wrong password."))
