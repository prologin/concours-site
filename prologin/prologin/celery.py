# See http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django
from celery import Celery
from django.conf import settings

app = Celery('prologin')

app.conf.broker_transport_options = {'fanout_prefix': True}
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
