from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from prologin.utils import get_slug
from captcha.fields import CaptchaField
from users.avatars import generate_avatar
from datetime import timedelta
import hashlib
import random
import os

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    slug = models.SlugField(max_length=16, db_index=True)
    title = models.CharField(max_length=16)
    address = models.TextField()
    postal_code = models.CharField(max_length=5)
    city = models.CharField(max_length=64)
    country = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=16)
    birthday = models.DateField(max_length=64, blank=True, null=True)
    newsletter = models.BooleanField()

class ActivationToken(models.Model):
    user = models.OneToOneField(User)
    slug = models.SlugField(max_length=56, db_index=True)
    expiration_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.expiration_date = timezone.now() + timedelta(hours=3)
            self.slug = hashlib.sha224(bytes(str(random.random()), 'ascii')).hexdigest()
        super(ActivationToken, self).save(*args, **kwargs)

class RegisterForm(forms.ModelForm):
    captcha = CaptchaField()
    newsletter = forms.BooleanField(required=False)
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'captcha')

class ProloginUser():
    def getShortName(self, name):
        slug = get_slug(name)
        try:
            UserProfile.objects.get(slug=slug)
        except UserProfile.DoesNotExist:
            return slug
        
        raise ValueError('%s: user with the same short name already exists' % slug)

    def generate_avatars(self, slug):
        avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars', slug)
        if not os.path.isdir(avatar_dir):
            os.makedirs(avatar_dir)

        for size in settings.AVATAR_SIZES:
            avatar_path = os.path.join(avatar_dir, '%s_%s.png' % (slug, size))
            avatar = generate_avatar(slug, settings.AVATAR_SIZES[size])
            avatar.save(avatar_path, 'PNG')

    def send_activation_email(self, profile, token):
        msg = render_to_response('users/activation_email.txt', {'profile': profile, 'token': token}).content
        send_mail('Bienvenue sur le site de Prologin', msg, 'noreply@prologin.org', [profile.user.email], fail_silently=False)

    def register(self, name, email, password, newsletter, active=False):
        slug = self.getShortName(name)
        
        user = User.objects.create_user(name, email, password)
        if not active:
            user.is_active = False
            token = ActivationToken(user=user)
            token.save()
        user.save()

        profile = UserProfile(user=user, slug=slug, newsletter=newsletter)
        profile.save()

        self.generate_avatars(slug)

        if not active:
            self.send_activation_email(profile, token)

        return profile
