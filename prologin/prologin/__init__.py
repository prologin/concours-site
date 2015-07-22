# See http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django
from prologin.celery import app as celery_app


default_app_config = 'prologin.apps.ProloginConfig'
