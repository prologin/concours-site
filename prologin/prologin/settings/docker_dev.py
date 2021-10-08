from .common import *
from datetime import datetime
import os

# You can use $ pwgen -y 64
SECRET_KEY = 'CHANGEME'

# SECURITY/PERFORMANCE WARNING: don't run with DEBUG turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

SITE_HOST = "localhost:8000"

# Mandatory settings:
PROLOGIN_EDITION = 2022
PROBLEMS_REPOSITORY_PATH = '/var/prologin/problems'
PROBLEMS_CORRECTORS = ("http://vm.prologin.org/run",)
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''


# Celery
BROKER_URL = "redis://prologin_redis:6379/0"
CELERY_RESULT_BACKEND = BROKER_URL

# Required by the documents module:
DOCUMENTS_REPOSITORY_PATH = '/var/prologin/documents'

# Required by the archives module:
ARCHIVES_REPOSITORY_PATH = '/var/prologin/archives'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'prologin',
        'USER': 'prologin',
        'PASSWORD': 'whocareslol',
        'HOST': 'prologin_site_db',
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

# Register GCC! as OAuth client
AUTH_TOKEN_CLIENTS = {
    'gcc': AuthTokenClient('GCC!', '//172.18.0.7:8001/user/auth/callback'),
}
