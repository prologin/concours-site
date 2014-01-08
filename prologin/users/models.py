from django.db.models.signals import pre_save, post_save
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from django.db import models
from django import forms
from users.avatars import generate_avatar
from captcha.fields import CaptchaField
from prologin.utils import get_slug
from datetime import timedelta
import hashlib
import random
import os

@receiver(pre_save, sender=User, dispatch_uid='check_name')
def check_name(sender, **kwargs):
    user = kwargs['instance']
    slug = get_slug(user.username)
    try:
        db_user = UserProfile.objects.get(slug=slug)
        if not user.id or db_user.id != user.id:
            raise ValueError('%s: user with the same slug already exists' % slug)
    except UserProfile.DoesNotExist:
        pass

@receiver(post_save, sender=User, dispatch_uid='sync_user_profile')
def sync_user_profile(sender, **kwargs):
    if kwargs['created']:
        user = kwargs['instance']
        slug = get_slug(user.username)

        profile = UserProfile(user=user, slug=slug, newsletter=False)
        profile.save()

        profile.generate_avatars()
        if not user.is_active:
            token = ActivationToken(user=user)
            token.save()
            profile.send_activation_email(token)

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

    def __str__(self):
        return self.user.__str__()

    def generate_avatars(self):
        avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars', self.slug)
        if not os.path.isdir(avatar_dir):
            os.makedirs(avatar_dir)

        for size in settings.AVATAR_SIZES:
            avatar_path = os.path.join(avatar_dir, '%s_%s.png' % (self.slug, size))
            avatar = generate_avatar(self.slug, settings.AVATAR_SIZES[size])
            avatar.save(avatar_path, 'PNG')

    def send_activation_email(self, token):
        msg = render_to_response('users/activation_email.txt', {'profile': self, 'token': token}).content
        send_mail('Bienvenue sur le site de Prologin', msg, 'noreply@prologin.org', [self.user.email], fail_silently=False)

    def setSlug(self):
        slug = get_slug(self.name)
        try:
            UserProfile.objects.get(slug=slug)
        except UserProfile.DoesNotExist:
            self.slug = slug
        raise ValueError('%s: user with the same short name already exists' % slug)

    @staticmethod
    def register(name, email, password, newsletter, is_active=False):
        user = User.objects.create_user(name, email, password)
        user.is_active = is_active
        user.save()

        profile = UserProfile.objects.get(user_id=user.id)
        profile.newsletter = newsletter
        profile.save()

        return profile
