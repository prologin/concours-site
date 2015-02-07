from .common import *
import os


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# You can generate a key using the following command:
# openssl rand 64 -base64 | sed "s/[/10lO#+=]//g" | tr -d "\n"; echo
SECRET_KEY = 'CHANGEME'

ALLOWED_HOSTS = ['127.0.0.1']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = DEBUG


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'dev.db.sqlite'),
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

EMAIL_HOST = 'smtp.free.fr'
EMAIL_HOST_USER = 'servicesam@free.fr'
