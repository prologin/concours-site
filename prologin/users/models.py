import base64
import hashlib
import json
import logging
import os
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.signals import user_logged_in
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import LANGUAGE_SESSION_KEY, ugettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from hijack.signals import hijack_started, hijack_ended
from timezone_field import TimeZoneField

from prologin.languages import Language
from prologin.models import (AddressableModel, GenderField,
                             CodingLanguageField, EnumField, ChoiceEnum)
from prologin.utils import upload_path, storage
from prologin.utils.models import ResizeOnSaveImageField

ACTIVATION_TOKEN_LENGTH = 32
logger = logging.getLogger('users.models')

overwrite_storage = storage.OverwriteStorage()


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


class UserActivation(ExportModelOperationsMixin('user_activation'), models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='activation')
    slug = models.SlugField(max_length=ACTIVATION_TOKEN_LENGTH, db_index=True)
    expiration_date = models.DateTimeField()

    objects = UserActivationManager()

    def is_valid(self):
        return timezone.now() < self.expiration_date


class ProloginUserManager(UserManager):
    def get_by_natural_key(self, username):
        try:
            return self.get(**{'{}__iexact'.format(self.model.USERNAME_FIELD): username})
        except self.model.MultipleObjectsReturned:
            logger.warning("MultipleObjectsReturned for username/email: %s", username)
            return super().get_by_natural_key(username)
        except self.model.DoesNotExist:
            return self.get(email__iexact=username)


class EducationStage(ChoiceEnum):
    middle_school = (0, _("Middle school"))
    high_school = (1, _("High school"))
    bac = (2, _("Bac"))
    bacp1 = (3, _("Bac+1"))
    bacp2 = (4, _("Bac+2"))
    bacp3 = (5, _("Bac+3"))
    bacp4 = (6, _("Bac+4"))
    bacp5 = (7, _("Bac+5"))
    bacp6 = (8, _("Bac+6 and after"))
    other = (9, _("Other"))
    former = (10, _("Former student"))

    @classmethod
    def _get_choices(cls):
        return tuple(m.value for m in cls)


class ProloginUser(
        ExportModelOperationsMixin('user'), AbstractUser, AddressableModel):

    @staticmethod
    def upload_seed(instance):
        return b'prologinuser/%d' % instance.pk

    def upload_avatar_to(self, *args, **kwargs):
        return upload_path('avatar', using=ProloginUser.upload_seed)(self, *args, **kwargs)

    def upload_picture_to(self, *args, **kwargs):
        return upload_path('picture', using=ProloginUser.upload_seed)(self, *args, **kwargs)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    gender = GenderField(blank=True, null=True, db_index=True)
    school_stage = EnumField(EducationStage, null=True, db_index=True,
                             blank=True, verbose_name=_("Educational stage"))
    phone = models.CharField(max_length=16, blank=True, verbose_name=_("Phone"))
    birthday = models.DateField(blank=True, null=True,
                                verbose_name=_("Birth day"))
    allow_mailing = models.BooleanField(default=True, blank=True, db_index=True,
                                        verbose_name=_("Allow Prologin to send me emails"),
                                        help_text=_("We only mail you to provide useful information "
                                                    "during the various stages of the contest. "
                                                    "We hate spam as much as you do!"))
    signature = models.TextField(blank=True, verbose_name=_("Signature"))
    preferred_language = CodingLanguageField(blank=True, db_index=True,
                                             verbose_name=_("Preferred coding language"))
    timezone = TimeZoneField(default=settings.TIME_ZONE, verbose_name=_("Time zone"))
    preferred_locale = models.CharField(max_length=8, blank=True, verbose_name=_("Locale"), choices=settings.LANGUAGES)

    avatar = ResizeOnSaveImageField(upload_to=upload_avatar_to,
                                    storage=overwrite_storage,
                                    fit_into=settings.PROLOGIN_MAX_AVATAR_SIZE,
                                    blank=True,
                                    verbose_name=_("Profile picture"))
    picture = ResizeOnSaveImageField(upload_to=upload_picture_to,
                                     storage=overwrite_storage,
                                     fit_into=settings.PROLOGIN_MAX_AVATAR_SIZE,
                                     blank=True,
                                     verbose_name=_("Official member picture"))

    # MD5 password from <2015 Drupal website
    legacy_md5_password = models.CharField(max_length=32, blank=True)

    objects = ProloginUserManager()

    @property
    def preferred_language_enum(self):
        return Language[self.preferred_language]

    @property
    def plaintext_password(self):
        return base64.urlsafe_b64encode(
            hashlib.sha1("{}{}{}".format(self.first_name, self.last_name, settings.PLAINTEXT_PASSWORD_SALT)
                                 .encode('utf-8')).digest()
        ).decode('ascii').translate(settings.PLAINTEXT_PASSWORD_DISAMBIGUATION)[:settings.PLAINTEXT_PASSWORD_LENGTH]

    @property
    def normalized_username(self):
        return slugify("{}{}".format(self.first_name[:1], self.last_name))

    @property
    def picture_or_avatar(self):
        if self.picture:
            return self.picture
        return self.avatar

    @property
    def unsubscribe_token(self):
        user_id = str(self.id).encode()
        secret = settings.SECRET_KEY.encode()
        return hashlib.sha256(user_id + secret).hexdigest()

    def has_partial_address(self):
        return any((self.address, self.city, self.country, self.postal_code))

    def has_complete_address(self):
        return all((self.address, self.city, self.country, self.postal_code))

    def has_complete_profile(self):
        return self.has_complete_address() and all((self.phone_number, self.birthday))

    def get_absolute_url(self):
        return reverse('users:profile', args=[self.pk])

    def get_unsubscribe_url(self):
        return '{}{}?uid={}&token={}'.format(settings.SITE_BASE_URL, reverse('users:unsubscribe'), self.id,
                                             self.unsubscribe_token)


# Yay, monkey-path that bitch, thank you Django!
ProloginUser._meta.get_field('email')._unique = True
ProloginUser._meta.get_field('email').blank = False
ProloginUser._meta.get_field('email').db_index = True


def assign_preferred_language(sender, user, request, **kwargs):
    if hasattr(request, 'user') and request.user.is_authenticated():
        request.session[LANGUAGE_SESSION_KEY] = request.user.preferred_locale

user_logged_in.connect(assign_preferred_language)


def _get_user_dict(user):
    return {
        'id': user.pk,
        'username': user.username,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'full_name': user.get_full_name(),
        'url': settings.SITE_BASE_URL + reverse('users:profile', args=[user.pk]),
    }


def notify_hijack_started(sender, **kwargs):
    s = settings.PROLOGIN_HIJACK_NOTIFY
    if not s:
        return
    try:
        data = {'event': 'start',
                'hijacker': _get_user_dict(kwargs['hijacker']),
                'hijacked': _get_user_dict(kwargs['hijacked'])}
        requests.request(s['method'], s['url'], data=json.dumps(data), **s.get('kwargs', {}))
    except Exception:
        logging.exception("Could not notify of hijack-started")


def notify_hijack_ended(sender, **kwargs):
    s = settings.PROLOGIN_HIJACK_NOTIFY
    if not s:
        return
    try:
        data = {'event': 'end',
                'hijacker': _get_user_dict(kwargs['hijacker']),
                'hijacked': _get_user_dict(kwargs['hijacked'])}
        requests.request(s['method'], s['url'], data=json.dumps(data), **s.get('kwargs', {}))
    except Exception:
        logging.exception("Could not notify of hijack-ended")


hijack_started.connect(notify_hijack_started)
hijack_ended.connect(notify_hijack_ended)
