from .common import *

PROLOGIN_SEMIFINAL_MODE = True

# How much time spent on a problem becomes concerning
# Format: a tuple of (warning amount, danger amount), amounts in seconds
SEMIFINAL_CONCERNING_TIME_SPENT = (30 * 60, 45 * 60)

# We won't use those in semifinal
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''

MIDDLEWARE_CLASSES = (
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # French by default for semifinals, avoid browsers misconfigurations
    # 'django.middleware.locale.LocaleMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'semifinal.middleware.SemifinalMiddleware',
)

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
    'django_bootstrap_breadcrumbs',
    'rules.apps.AutodiscoverRulesConfig',

    # Prologin apps
    'semifinal',  # must stay at the top
    'prologin',
    'centers',
    'contest',
    'problems',
    'schools',
    'users',

    # Django and vendor, at the bottom for template overriding
    'django.contrib.admin',
)

ROOT_URLCONF = 'semifinal.urls'
