import redis
from django.conf import settings
from django.core.management import BaseCommand

import archives.models
from archives.flickr import Flickr


class Command(BaseCommand):
    help = "Download Flickr album photos for all archives and cache the URLs in Redis."

    def handle(self, *args, **options):
        flickr = Flickr(*settings.ARCHIVES_FLICKR_CREDENTIALS)

        cred = settings.ARCHIVES_FLICKR_REDIS_STORE.copy()
        cred.pop('prefix')
        store = redis.StrictRedis(**cred)

        for archive in sorted(archives.models.Archive.all_archives()):
            photos = list(archive.final.get_flickr_photos(flickr=flickr))
            key = archive.final._flickr_redis_key()
            store.delete(key)
            for photo in photos:
                store.lpush(key, photo['url_sq'])

            self.stdout.write("Stored {} photos for {}".format(len(photos), archive))
