import base64
import hashlib
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from timezone_field import TimeZoneField

from prologin.models import AddressableModel, GenderField, CodingLanguageField
from prologin.languages import Language
from prologin.utils import upload_path

ACTIVATION_TOKEN_LENGTH = 32


class InvalidActivationError(Exception):
    pass


class UserActivationManager(models.Manager):
    def register(self, user):
        expiration_date = timezone.now() + settings.USER_ACTIVATION_EXPIRATION
        slug = base64.urlsafe_b64encode(os.urandom(ACTIVATION_TOKEN_LENGTH))
        slug = slug.decode('ascii')[:ACTIVATION_TOKEN_LENGTH]
        activation = self.model(user=user, slug=slug, expiration_date=expiration_date)
        activation.save()
        return activation

    def activate(self, slug):
        try:
            activation = self.get(slug=slug)
        except self.model.DoesNotExist:
            raise InvalidActivationError("No such {}".format(self.model.__class__.__name__))
        if not activation.is_valid():
            raise InvalidActivationError("{} is obsolete".format(self.model.__class__.__name__))
        user = activation.user
        user.is_active = True
        user.save()
        activation.delete()
        return user

    def expired_users(self):
        return get_user_model().objets.filter(is_active=False, activation__expiration_date__lt=timezone.now())


class UserActivation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='activation')
    slug = models.SlugField(max_length=ACTIVATION_TOKEN_LENGTH, db_index=True)
    expiration_date = models.DateTimeField()

    objects = UserActivationManager()

    def is_valid(self):
        return timezone.now() < self.expiration_date


class ProloginUser(AbstractUser, AddressableModel):
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    gender = GenderField(blank=True, null=True, db_index=True)
    school_stage = models.CharField(max_length=128, blank=True, verbose_name=_("Educational stage"))
    phone = models.CharField(max_length=16, blank=True, verbose_name=_("Phone"))
    birthday = models.DateField(blank=True, null=True, verbose_name=_("Birth day"))
    newsletter = models.BooleanField(default=False, blank=True, db_index=True,
                                     verbose_name=_("Subscribe to the newsletter"))
    allow_mailing = models.BooleanField(default=True, blank=True, db_index=True,
                                        verbose_name=_("Allow Prologin to send me emails"),
                                        help_text=_("We only mail you to provide useful information "
                                                    "during the various stages of the contest. "
                                                    "We hate spam as much as you do!"))
    signature = models.TextField(blank=True, verbose_name=_("Signature"))
    preferred_language = CodingLanguageField(blank=True, null=True, db_index=True, verbose_name=_("Preferred coding language"))
    timezone = TimeZoneField(default=settings.TIME_ZONE, verbose_name=_("Time zone"))
    preferred_locale = models.CharField(max_length=8, blank=True, verbose_name=_("Locale"))

    avatar = models.ImageField(upload_to=upload_path('avatar'), blank=True, verbose_name=_("Profile picture"))
    picture = models.ImageField(upload_to=upload_path('picture'), blank=True, verbose_name=_("Official member picture"))

    # MD5 password from <2015 Drupal website
    legacy_md5_password = models.CharField(max_length=32, blank=True)

    @property
    def preferred_language_def(self):
        return Language[self.preferred_language].value

    @property
    def plaintext_password(self):
        return base64.urlsafe_b64encode(
            hashlib.sha1("{}{}{}".format(self.first_name, self.last_name, settings.PLAINTEXT_PASSWORD_SALT)
                                 .encode('utf-8')).digest()
        ).decode('ascii').translate(settings.PLAINTEXT_PASSWORD_DISAMBIGUATION)[:settings.PLAINTEXT_PASSWORD_LENGTH]

    @property
    def picture_or_avatar(self):
        if self.picture:
            return self.picture
        return self.avatar

    def has_partial_address(self):
        return any((self.address, self.city, self.country, self.postal_code))

    def has_complete_address(self):
        return all((self.address, self.city, self.country, self.postal_code))

    def has_complete_profile(self):
        return self.has_complete_address() and all((self.phone_number, self.birthday))


# Yay, monkey-path that bitch, thank you Django!
ProloginUser._meta.get_field('email')._unique = True
ProloginUser._meta.get_field('email').blank = False
ProloginUser._meta.get_field('email').db_index = True
