from .semifinal_common import *
import os

# You can use $ pwgen -y 64
SECRET_KEY = 'CHANGEME'

# SECURITY/PERFORMANCE WARNING: don't run with DEBUG turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '::1', 'localhost', 'testserver']
INTERNAL_IPS = ALLOWED_HOSTS

# Set the right hostname, as seen by contestant's machines
SITE_HOST = "localhost:8000"

# Current edition
PROLOGIN_EDITION = 2019

# Repository paths
PROBLEMS_REPOSITORY_PATH = os.path.join(PROJECT_ROOT_DIR, '..', 'problems')

# Camisole url
PROBLEMS_CORRECTORS = ('http://localhost:42920/run',)


# These should be OK (assuming no TLS)
PROBLEMS_CHALLENGE_WHITELIST = ('demi{}'.format(PROLOGIN_EDITION),)
SITE_BASE_URL = 'http://{}'.format(SITE_HOST)

# Uncomment and modify if needed:

# Time before a new problem is automatically unlocked to help pass the
# current level
# PROBLEMS_DEFAULT_AUTO_UNLOCK_DELAY = 15 * 60

# How much time spent on a problem becomes concerning
# Format: a tuple of (warning amount, danger amount), amounts in seconds
# SEMIFINAL_CONCERNING_TIME_SPENT = (30 * 60, 45 * 60)

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'prologin',
    }
}
