from .common import *
import os

# You can use $ pwgen -y 64
SECRET_KEY = 'CHANGEME'

# SECURITY/PERFORMANCE WARNING: don't run with DEBUG turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '::1', 'localhost', 'testserver']
INTERNAL_IPS = ALLOWED_HOSTS

SITE_HOST = "localhost:8000"

# Current edition
PROLOGIN_EDITION = 2019

# Repository paths
PROBLEMS_REPOSITORY_PATH = os.path.join(PROJECT_ROOT_DIR, '..', 'problems')
DOCUMENTS_REPOSITORY_PATH = os.path.join(PROJECT_ROOT_DIR, '..', 'documents')
ARCHIVES_REPOSITORY_PATH = os.path.join(PROJECT_ROOT_DIR, '..', 'archives')

# Camisole url
PROBLEMS_CORRECTORS = ('http://vm.prologin.org/run',)

# OAuth server
AUTH_TOKEN_CLIENTS = {
    'gcc': AuthTokenClient('CHANGEME', '//localhost:8001/user/auth/callback'),
}

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'prologin',
    }
}

# Logging
# https://docs.djangoproject.com/en/1.7/topics/logging/

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


# Email
# Run debug server with:
#   $ make stmpserver

EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False


# Recaptcha

RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''

# Enable / disable the countdown
COUNTDOWN_ENABLED = True

