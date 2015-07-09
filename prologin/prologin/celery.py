# See http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django
from celery import Celery
from django.conf import settings

app = Celery('prologin')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print("Request: {:!r}".format(self.request))
