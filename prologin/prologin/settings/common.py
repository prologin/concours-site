"""
Django common settings for prologin project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from collections import namedtuple
import datetime
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []

SITE_ID = 1


# Databases
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
    },
    'mysql_legacy': {
        'ENGINE': 'mysql.connector.django',
        'HOST': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
    },
}


# Application definition

INSTALLED_APPS = (
    # Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Vendor
    'bootstrapform',
    'captcha',
    'django_bootstrap_breadcrumbs',
    'django_comments',
    'djmail',
    'ordered_model',
    'macros',
    'mptt',
    'tagging',

    # Prologin apps
    'prologin',
    'centers',
    'contest',
    'documents',
    'homepage',
    'qcm',
    'news',
    'pages',
    'problems',
    'sponsor',
    'team',
    'users',

    # Django and vendor, at the bottom for template overriding
    'django.contrib.admin',
    'zinnia',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'prologin.middleware.ContestMiddleware',
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

LANGUAGE_CODE = 'fr'

LANGUAGES = (
    ('en', _("English")),
    ('fr', _("French")),
)

TIME_ZONE = 'Europe/Paris'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

USE_I18N = True

USE_L10N = True

USE_TZ = True

MIGRATION_MODULES = {
    'zinnia': 'news.migrations_zinnia',
}

# Celery (task scheduler)

BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_RESULT_BACKEND = BROKER_URL  # also use redis to store the results
CELERY_RESULT_PERSISTENT = True  # keep results on broker restart
CELERY_TASK_RESULT_EXPIRES = 3600 * 12  # 12 hours

# Emails

DJMAIL_BODY_TEMPLATE_PROTOTYPE = "{name}.body.{type}.{ext}"
DJMAIL_SUBJECT_TEMPLATE_PROTOTYPE = "{name}.subject.{ext}"
DJMAIL_REAL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_BACKEND = "djmail.backends.async.EmailBackend"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'


# Media files (uploaded)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


# Authentication

AUTHENTICATION_BACKENDS = (
    'prologin.backends.ModelBackendWithLegacy',
)
AUTH_USER_MODEL = 'users.ProloginUser'

LOGIN_URL = reverse_lazy('users:login')
LOGOUT_URL = reverse_lazy('users:logout')
LOGIN_REDIRECT_URL = reverse_lazy('home')
USER_ACTIVATION_EXPIRATION = datetime.timedelta(days=7)


# Prologin specific

SITE_HOST = 'www.prologin.org'
PROLOGIN_CONTACT_MAIL = 'info@prologin.org'
DEFAULT_FROM_EMAIL = PROLOGIN_CONTACT_MAIL
PROLOGIN_MAX_AGE = 21
PROLOGIN_MAX_LEVEL_DIFFICULTY = 9
PROLOGIN_SEMIFINAL_MIN_WISH_COUNT = 3
LATEX_GENERATION_PROC_TIMEOUT = 60  # in seconds
PLAINTEXT_PASSWORD_LENGTH = 8
PLAINTEXT_PASSWORD_DISAMBIGUATION = str.maketrans("iIl1oO0/+=", "aAbcCD9234")
PLAINTEXT_PASSWORD_SALT = "whatever1337leet"
FINAL_EVENT_DATE_FORMAT = 'l d'

# Cache durations and keys
CacheSetting = namedtuple('CacheSetting', 'key duration')
PROLOGIN_CACHES = {
    'challenge_list': CacheSetting('problems.challenge_list', 3600),
    'challenge_details': CacheSetting('problems.challenge_details.{name}', 3600),
}

# Prologin correction system
# List of strings (tried in order for load-balancing/fallback):
#  - if local: 'local:///path/to/prefix'
#  - if remote: 'http://thehost:55080/submit'
TRAINING_CORRECTORS = (
)

# How long to wait, in seconds, before displaying the submission result page.
# Don't use a too small value because the corrector system will most of the time
# not have the time to compile & run the tests.
# Don't use a too large value because it makes the page load for too long.
TRAINING_RESULT_TIMEOUT = 3
# Interval, in milliseconds, between checks for results in the submission page
# (this is done using Javascript).
TRAINING_RESULT_POLL_INTERVAL = 3 * 1000

# List of challenges (directory name), eg. ('demi2015', 'qcm2014')
# Empty list allows everything
TRAINING_CHALLENGE_WHITELIST = ()
TRAINING_PROBLEM_REPOSITORY_PATH = os.path.join(BASE_DIR, 'problems')


# Recaptcha

NOCAPTCHA = True
RECAPTCHA_USE_SSL = True


# Zinnia (news)

HOMEPAGE_ARTICLES = 4
ZINNIA_AUTO_CLOSE_COMMENTS_AFTER = 0  # disable comments
ZINNIA_ENTRY_BASE_MODEL = 'news.models.NewsEntry'
ZINNIA_FEEDS_FORMAT = 'atom'
ZINNIA_FEEDS_MAX_ITEMS = 20
ZINNIA_MAIL_COMMENT_AUTHORS = False
ZINNIA_MARKUP_LANGUAGE = 'markdown'
ZINNIA_PING_DIRECTORIES = ()
ZINNIA_PING_EXTERNAL_URLS = False
ZINNIA_PROTOCOL = 'https'
ZINNIA_SAVE_PING_DIRECTORIES = False
