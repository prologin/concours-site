from .common import *
import os

# You can use $ pwgen -y 64
SECRET_KEY = 'CHANGEME'

# SECURITY/PERFORMANCE WARNING: don't run with DEBUG turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '::1', 'localhost']

SITE_HOST = "localhost:8000"

# Mandatory settings:
# PROLOGIN_EDITION = 2018
# PROBLEMS_REPOSITORY_PATH = '/path/to/problems'
# PROBLEMS_CORRECTORS = ()
# RECAPTCHA_PUBLIC_KEY = ''
# RECAPTCHA_PRIVATE_KEY = ''

# Required by the documents module:
# DOCUMENTS_REPOSITORY_PATH = '/path/to/documents'

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
