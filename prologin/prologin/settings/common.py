"""
Django common settings for prologin project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy
import datetime
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []

SITE_ID = 1

# Application definition

INSTALLED_APPS = (
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Vendor
    'bootstrapform',
    'macros',
    'mptt',
    'tagging',

    # Prologin
    'captcha',
    'homepage',
    'news',
    'prologin',
    'team',
    'users',

    # Vendor (for overwriting)
    'zinnia',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'zinnia.context_processors.version',
)

ROOT_URLCONF = 'prologin.urls'

WSGI_APPLICATION = 'prologin.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'fr-FR'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'


# Media files (uploaded)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


# Authentication
AUTH_USER_MODEL = 'users.ProloginUser'
LOGIN_URL = reverse_lazy('users:login')
LOGOUT_URL = reverse_lazy('users:logout')
LOGIN_REDIRECT_URL = '/'


# Prologin specific
SITE_HOST = 'www.prologin.org'
PROLOGIN_CONTACT_MAIL = "info@prologin.org"
PROLOGIN_EDITION = 2015
USER_ACTIVATION_MAIL_SUBJECT = _("Activez votre compte Prologin")
USER_ACTIVATION_EXPIRATION = datetime.timedelta(hours=12)


# Zinnia (news)
HOMEPAGE_ARTICLES = 3
ZINNIA_ENTRY_BASE_MODEL = 'news.models.NewsEntry'
ZINNIA_FEEDS_FORMAT = 'atom'
ZINNIA_FEEDS_MAX_ITEMS = 20
ZINNIA_MAIL_COMMENT_AUTHORS = False
ZINNIA_MARKUP_LANGUAGE = 'markdown'
ZINNIA_PING_DIRECTORIES = ()
ZINNIA_PING_EXTERNAL_URLS = False
ZINNIA_PROTOCOL = 'https'
ZINNIA_SAVE_PING_DIRECTORIES = False
