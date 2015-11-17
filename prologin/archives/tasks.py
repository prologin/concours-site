from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
import random

import archives.models
import redis

logger = get_task_logger('prologin.archives')


@shared_task(bind=True)
def extract_archive_flickr_photos(self):
    cred = settings.ARCHIVES_FLICKR_REDIS_STORE.copy()
    cred.pop('prefix')
    store = redis.StrictRedis(**cred)

    for archive in archives.models.Archive.all_archives():
        photos = list(archive.final.get_flickr_photos())
        random.shuffle(photos)
        key = archive.final._flickr_redis_key()
        store.delete(key)
        for photo in photos:
            store.lpush(key, photo['url_sq'])
        logger.info("Stored %d photos for %s", len(photos), archive)
