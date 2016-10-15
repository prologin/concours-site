"""
Django common settings for prologin project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

from django.core.urlresolvers import reverse_lazy
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _
from collections import namedtuple
import datetime
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

SITE_ID = 1


# Databases
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'HOST': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
    },
    # Uncomment if you need to migrate some data from the old drupal website
    # 'mysql_legacy': {
    #     'ENGINE': 'mysql.connector.django',
    #     'HOST': '',
    #     'NAME': '',
    #     'USER': '',
    #     'PASSWORD': '',
    # },
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
    'bootstrap3',
    'captcha',
    'compat',
    'datatableview',
    'django_bootstrap_breadcrumbs',
    'django_comments',
    'django_prometheus',
    'djmail',
    'hijack',
    'mptt',
    'reversion',
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
    'marauder',
    'news',
    'pages',
    'problems',
    'schools',
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'zinnia.context_processors.version',
            ],
        },
    },
]

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
    'problems.staticfinder.ProblemsStaticFinder',
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
SITE_HOST = 'prologin.org'
SITE_BASE_URL = 'https://{}'.format(SITE_HOST)
PROLOGIN_CONTACT_MAIL = 'info@prologin.org'
DEFAULT_FROM_EMAIL = 'Prologin <{}>'.format(PROLOGIN_CONTACT_MAIL)
PROLOGIN_EDITION = None
PROLOGIN_MAX_AVATAR_SIZE = 220
PROLOGIN_MAX_AGE = 21
PROLOGIN_MAX_LEVEL_DIFFICULTY = 9
PROLOGIN_SEMIFINAL_MIN_WISH_COUNT = 1
PROLOGIN_SEMIFINAL_MAX_WISH_COUNT = 3
PROLOGIN_VM_VERSION_PATH = 'http://vm.prologin.org/versions'
PROLOGIN_BUG_TRACKER_URL = 'https://bitbucket.org/prologin/site-issues/issues?status=new&status=open'
LATEX_GENERATION_PROC_TIMEOUT = 60  # in seconds
PLAINTEXT_PASSWORD_LENGTH = 8
PLAINTEXT_PASSWORD_DISAMBIGUATION = str.maketrans("iIl1oO0/+=-_", "aAbcCD9234z5")
PLAINTEXT_PASSWORD_SALT = "whatever1337leet"
FINAL_EVENT_DATE_FORMAT = 'l d'
GOOGLE_ANALYTICS_ID = ''
PROLOGIN_UTILITY_REDIS_STORE = dict(host='localhost', port=6379, db=0, socket_connect_timeout=1, socket_timeout=3)
PROLOGIN_WEBHOOK_BASE_URL = 'https://webhook.prologin.org'
PROLOGIN_WEBHOOK_SECRET = 'changeme'
PROBLEMS_DEFAULT_AUTO_UNLOCK_DELAY = 15 * 60  # in seconds; 15 minutes
PROLOGIN_SEMIFINAL_MODE = False

# Cache durations and keys
CacheSetting = namedtuple('CacheSetting', 'key duration')
PROLOGIN_CACHES = {
    'problems:compilers:versions': CacheSetting('problems:compilers:versions', 3600 * 24),
}

# Prologin correction system
# List of strings (tried in order for load-balancing/fallback):
#  - if local: 'local:///path/to/prefix'
#  - if remote: 'http://thehost:55080/submit'
PROBLEMS_CORRECTORS = (
)

# Max size of uploaded source files in bytes
PROBLEMS_UPLOAD_MAX_LENGTH = 1 << 21  # 2MiB
# How long to wait, in seconds, for a remote corrector
PROBLEMS_CORRECTOR_REQUEST_TIMEOUT = 10 * 60
# How long to wait, in seconds, before displaying the submission result page.
# Don't use a too small value because the corrector system will most of the time
# not have the time to compile & run the tests.
# Don't use a too large value because it makes the page load for too long.
PROBLEMS_RESULT_TIMEOUT = 3
# Interval, in milliseconds, between checks for results in the submission page
# (this is done using Javascript).
PROBLEMS_RESULT_POLL_INTERVAL = 3 * 1000

# Storage path for temporary files for semifinal data imports
DATA_IMPORT_SEMIFINAL_TEMPORARY_DIR = '/tmp/data-import/semifinal'

# List of challenges (directory name), eg. ('demi2015', 'qcm2014')
# Empty list allows everything
PROBLEMS_CHALLENGE_WHITELIST = ()
PROBLEMS_REPOSITORY_PATH = os.path.join(BASE_DIR, 'problems')
PROBLEMS_REPOSITORY_STATIC_PREFIX = 'problems'

# Path to archives repository (sub-folders shall be years)
ARCHIVES_REPOSITORY_PATH = os.path.join(BASE_DIR, 'archives')
ARCHIVES_REPOSITORY_STATIC_PREFIX = 'archives'
ARCHIVES_FLICKR_REDIS_KEY = 'prologin.archives.photos.{year}.{suffix}'
ARCHIVES_FLICKR_CREDENTIALS = ('username', 'api-key', 'secret')
ARCHIVES_FLICKR_ALBUM_URL = 'https://www.flickr.com/photos/prologin/albums/{id}'

# Path to contestant final homes (for download)
HOMES_PATH = ''

# Staff correction stuff

CORRECTION_LIVE_UPDATE_REDIS_KEY = 'prologin.correction.liveupdate.{key}'
CORRECTION_LIVE_UPDATE_POLL_INTERVAL = 5  # seconds
CORRECTION_LIVE_UPDATE_TIMEOUT = CORRECTION_LIVE_UPDATE_POLL_INTERVAL * 2  # offline if misses two pings


# Recaptcha

NOCAPTCHA = True
RECAPTCHA_USE_SSL = True
RECAPTCHA_KEY = ''

# Hijack (impersonation)

HIJACK_DISPLAY_ADMIN_BUTTON = False
HIJACK_DECORATOR = 'users.rules.hijack_forbidden'
HIJACK_AUTHORIZATION_CHECK = 'users.rules.hijack_authorization_check'
HIJACK_LOGIN_REDIRECT_URL = '/'
HIJACK_LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL
PROLOGIN_HIJACK_NOTIFY = False
# {'method': 'post', 'url': '/django/impersonate', 'kwargs': {'timeout': (1, 1)}}

PROLOGIN_NEW_SCHOOL_NOTIFY = False

# Debug toolbar

DEBUG_TOOLBAR_CONFIG = {
    # Already served
    'JQUERY_URL': '',
    'DISABLE_PANELS': {'debug_toolbar.panels.redirects.RedirectsPanel',
                       # StaticFilesPanel takes *way* too much compute power while being useless
                       'debug_toolbar.panels.staticfiles.StaticFilesPanel'},
}

# Content Security Policy
# FIXME: this is too restrictive, disabled
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_FONT_SRC = ("'self'", "fonts.gstatic.com", "cdn.mathjax.org",)
# CSP_FRAME_SRC = ("'self'", "*.google.com", "player.vimeo.com",)
# CSP_IMG_SRC = ("*",)
# CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "*.googleapis.com", "*.gstatic.com", "*.google.com", "cdn.mathjax.org",)
# CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "*.googleapis.com",)

BOOTSTRAP3 = {'success_css_class': ''}

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


# Marauder

MARAUDER_GCM_KEY = ""


# Facebook

FACEBOOK_GRAPH_API_ACCESS_TOKEN = ""
