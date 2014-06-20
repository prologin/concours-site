from django.db.models.signals import post_save
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.dispatch import receiver
from django.forms import ModelForm
from django.utils import timezone
from django.db import models
from django import forms
from captcha.fields import CaptchaField
from datetime import timedelta
import base64
import os

@receiver(post_save, sender=User, dispatch_uid='sync_user_profile')
def sync_user_profile(sender, **kwargs):
    user = kwargs['instance']
    if kwargs['created']:
        profile = UserProfile(user=user)
        profile.save()

    if not user.is_active:
        token = ActivationToken(user=user)
        token.save()
        user.profile.send_activation_email(token)

class ActivationToken(models.Model):
    user = models.OneToOneField(User)
    slug = models.SlugField(max_length=32, db_index=True)
    expiration_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.expiration_date = timezone.now() + timedelta(hours=3)
            self.slug = base64.urlsafe_b64encode(os.urandom(32))[:32].decode('ascii')
        return super(ActivationToken, self).save(*args, **kwargs)

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    address = models.TextField(blank=True, null=True)
    postal_code = models.CharField(max_length=5, blank=True, null=True)
    city = models.CharField(max_length=64, blank=True, null=True)
    country = models.CharField(max_length=64, blank=True, null=True)
    phone_number = models.CharField(max_length=16, blank=True, null=True)
    birthday = models.DateField(max_length=64, blank=True, null=True)
    newsletter = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.user.__str__()

    def send_activation_email(self, token):
        msg = render_to_response('users/activation_email.txt', {'profile': self, 'token': token}).content.decode('utf-8')
        send_mail('Bienvenue sur le site de Prologin', msg, 'noreply@prologin.org', [self.user.email], fail_silently=False)

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ('address', 'postal_code', 'city', 'country', 'phone_number', 'birthday', 'newsletter')

class UserSimpleForm(ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class RegisterForm(forms.ModelForm):
    captcha = CaptchaField()
    newsletter = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'newsletter', 'captcha')
