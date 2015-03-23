from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from prologin.models import AddressableModel, GenderField, CodingLanguageField
from prologin.utils import upload_path
from timezone_field import TimeZoneField
import base64
import hashlib
import os

ACTIVATION_TOKEN_LENGTH = 32


class ActivationTokenManager(models.Manager):
    def create_token(self, user):
        expiration_date = timezone.now() + settings.USER_ACTIVATION_EXPIRATION
        slug = base64.urlsafe_b64encode(os.urandom(ACTIVATION_TOKEN_LENGTH))
        slug = slug[:ACTIVATION_TOKEN_LENGTH].decode('ascii')
        return ActivationToken(user=user, slug=slug, expiration_date=expiration_date)


class ActivationToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    slug = models.SlugField(max_length=ACTIVATION_TOKEN_LENGTH, db_index=True)
    expiration_date = models.DateTimeField()

    objects = ActivationTokenManager()

    def is_valid(self):
        return timezone.now() < self.expiration_date


class ProloginUser(AbstractUser, AddressableModel):
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    gender = GenderField(blank=True, null=True, db_index=True)
    school_stage = models.CharField(max_length=128, blank=True, verbose_name=_("Educational stage"))
    phone = models.CharField(max_length=16, blank=True, verbose_name=_("Phone"))
    birthday = models.DateField(blank=True, null=True, verbose_name=_("Birth day"))
    newsletter = models.BooleanField(default=False, blank=True, db_index=True, verbose_name=_("Subscribe to the newsletter"))
    allow_mailing = models.BooleanField(default=True, blank=True, db_index=True, verbose_name=_("Allow Prologin to send emails"))
    signature = models.TextField(blank=True, verbose_name=_("Signature"))
    preferred_language = CodingLanguageField(blank=True, null=True, db_index=True, verbose_name=_("Preferred coding language"))
    timezone = TimeZoneField(default=settings.TIME_ZONE, verbose_name=_("Time zone"))
    preferred_locale = models.CharField(max_length=8, blank=True, verbose_name=_("Locale"))

    avatar = models.ImageField(upload_to=upload_path('avatar'), blank=True, verbose_name=_("Profile picture"))
    picture = models.ImageField(upload_to=upload_path('picture'), blank=True, verbose_name=_("Official member picture"))

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

    def send_activation_email(self, token):
        url = 'https://{host}{path}'.format(
            host=settings.SITE_HOST,
            path=reverse('users:activate', args=[self.pk, token.slug]))
        self.email_user(
            _("Activate your Prologin account"),
            render_to_string('users/activation_email.txt', {'user': self, 'token': token, 'url': url}),
            from_email=settings.PROLOGIN_CONTACT_MAIL,
            fail_silently=False)


# Yay, monkey-path that bitch, thank you Django!
ProloginUser._meta.get_field('email')._unique = True
ProloginUser._meta.get_field('email').blank = False
ProloginUser._meta.get_field('email').db_index = True
