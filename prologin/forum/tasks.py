import requests
import json
from django.conf import settings
from celery import shared_task


@shared_task(bind=True, ignore_result=True, default_retry_delay=60, max_retries=3)
def notify_new_thread(self, thread: dict):
    r = requests.post(settings.PROLOGIN_WEBHOOK_BASE_URL + '/django/forum',
                      data=json.dumps(thread),
                      headers={'Authorization': settings.PROLOGIN_WEBHOOK_SECRET})
    if not r.ok:
        raise ValueError("Remote replied with status {}".format(r.status_code))
