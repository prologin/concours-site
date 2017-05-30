from .common import *

SECRET_KEY = 'foo'

LANGUAGE_CODE = 'en'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        # 'ENGINE': 'django.db.backends.postgresql',
        # 'NAME': 'prologin',
        # 'USER': 'prologin',
        # 'PASSWORD': 'foobar',
        # 'TEST': {
        #     'NAME': 'prologin_test',
        # },
    },
}

PROLOGIN_EDITION = 2017
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''
