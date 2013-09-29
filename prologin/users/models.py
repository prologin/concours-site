from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from prologin.utils import get_slug
from captcha.fields import CaptchaField
from users.avatars import generate_avatar
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

class ProloginUser():
    def getShortName(self, name):
        slug = get_slug(name)
        try:
            UserProfile.objects.get(slug=slug)
        except UserProfile.DoesNotExist:
            return slug
        
        raise ValueError('%s: user with the same short name already exists' % slug)

    def register(self, name, email, password, newsletter):
        slug = self.getShortName(name)
        
        user = User.objects.create_user(name, email, password)
        user.save()

        profile = UserProfile(user=user, slug=slug, newsletter=newsletter)
        profile.save()

        avatar_dir = '%susers/static/users/avatars/%s/' % (settings.SITE_ROOT, profile.slug)
        if not os.path.isdir(avatar_dir):
            os.makedirs(avatar_dir)
        for size in settings.AVATAR_SIZES:
            avatar_path = '%s%s_%s.png' % (avatar_dir, profile.slug, size)
            avatar = generate_avatar(profile.slug)
            avatar.save(avatar_path, 'PNG')
        
        return profile

class RegisterForm(forms.ModelForm):
    captcha = CaptchaField()
    newsletter = forms.BooleanField(required=False)
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'captcha')
