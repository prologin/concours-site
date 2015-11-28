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
    'adminsortable',
    'bootstrapform',
    'captcha',
    'django_bootstrap_breadcrumbs',
    'django_comments',
    'django_prometheus',
    'djmail',
    'mptt',
    'rules.apps.AutodiscoverRulesConfig',
    'statictemplate',
    'tagging',

    # Prologin apps
    'prologin',
    'archives',
    'centers',
    'contest',
    'documents',
    'forum',
    'homepage',
    'qcm',
    'mailing',
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
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'prologin.middleware.ContestMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
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

FORMAT_MODULE_PATH = [
    'formats',
]

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

PROJECT_ROOT_DIR = os.path.dirname(BASE_DIR)

STATIC_ROOT = os.path.join(PROJECT_ROOT_DIR, 'public', 'static')
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'problems.staticfinder.TrainingStaticFinder',
    'archives.staticfinder.ArchivesStaticFinder',
)


# Media files (uploaded)

MEDIA_ROOT = os.path.join(PROJECT_ROOT_DIR, 'public', 'media')
MEDIA_URL = '/media/'


# Authentication

AUTHENTICATION_BACKENDS = (
    'prologin.backends.ModelBackendWithLegacy',
    'rules.permissions.ObjectPermissionBackend',
)
AUTH_USER_MODEL = 'users.ProloginUser'

LOGIN_URL = reverse_lazy('users:login')
LOGOUT_URL = reverse_lazy('users:logout')
LOGIN_REDIRECT_URL = reverse_lazy('home')
USER_ACTIVATION_EXPIRATION = datetime.timedelta(days=7)

# Forum

FORUM_THREADS_PER_PAGE = 25
FORUM_POSTS_PER_PAGE = 20
FORUM_MENTIONS_PER_MESSAGE = 3  # @mention limit to prevent database DoS

# Prologin specific

SITE_HOST = 'www.prologin.org'
PROLOGIN_CONTACT_MAIL = 'info@prologin.org'
DEFAULT_FROM_EMAIL = 'Prologin <{}>'.format(PROLOGIN_CONTACT_MAIL)
PROLOGIN_MAX_AGE = 21
PROLOGIN_MAX_LEVEL_DIFFICULTY = 9
PROLOGIN_SEMIFINAL_MIN_WISH_COUNT = 1
PROLOGIN_SEMIFINAL_MAX_WISH_COUNT = 3
PROLOGIN_VM_VERSION_PATH = 'http://vm.prologin.org/versions'
LATEX_GENERATION_PROC_TIMEOUT = 60  # in seconds
PLAINTEXT_PASSWORD_LENGTH = 8
PLAINTEXT_PASSWORD_DISAMBIGUATION = str.maketrans("iIl1oO0/+=", "aAbcCD9234")
PLAINTEXT_PASSWORD_SALT = "whatever1337leet"
FINAL_EVENT_DATE_FORMAT = 'l d'
GOOGLE_ANALYTICS_ID = ''

# Cache durations and keys
CacheSetting = namedtuple('CacheSetting', 'key duration')
PROLOGIN_CACHES = {
    'problems:compilers:versions': CacheSetting('problems:compilers:versions', 3600 * 24),
}

# Prologin correction system
# List of strings (tried in order for load-balancing/fallback):
#  - if local: 'local:///path/to/prefix'
#  - if remote: 'http://thehost:55080/submit'
TRAINING_CORRECTORS = (
)

# Max size of uploaded source files in bytes
TRAINING_UPLOAD_MAX_LENGTH = 1 << 21  # 2MiB
# How long to wait, in seconds, for a remote corrector
TRAINING_CORRECTOR_REQUEST_TIMEOUT = 5
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
TRAINING_PROBLEM_REPOSITORY_STATIC_PREFIX = 'problems'

# Path to archives repository (sub-folders shall be years)
ARCHIVES_REPOSITORY_PATH = os.path.join(BASE_DIR, 'archives')
ARCHIVES_REPOSITORY_STATIC_PREFIX = 'archives'
ARCHIVES_FLICKR_REDIS_STORE = dict(host='localhost', port=6379, db=1, prefix='prologin.archives.photos')
ARCHIVES_FLICKR_CREDENTIALS = ('username', 'api-key', 'secret')
ARCHIVES_FLICKR_ALBUM_URL = 'https://www.flickr.com/photos/prologin/albums/%(id)s'

# Recaptcha

NOCAPTCHA = True
RECAPTCHA_USE_SSL = True


# Content Security Policy

CSP_DEFAULT_SRC = ("'self'",)
CSP_FONT_SRC = ("'self'", "fonts.gstatic.com", "cdn.mathjax.org",)
CSP_FRAME_SRC = ("'self'", "*.google.com", "player.vimeo.com",)
CSP_IMG_SRC = ("*",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "*.googleapis.com", "*.gstatic.com", "*.google.com", "cdn.mathjax.org",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "*.googleapis.com",)

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
ZINNIA_AUTO_CLOSE_PINGBACKS_AFTER = 0  # disables pingbacks completely
ZINNIA_AUTO_CLOSE_TRACKBACKS_AFTER = 0  # disables trackbacks completely
