import redis
from django.conf import settings
from django.core.management import BaseCommand

import archives.models
from archives.flickr import Flickr

FINAL_NAME = "{} Finale"


class Command(BaseCommand):
    help = "Download Flickr album photos for all archives and cache the URLs in Redis."

    def handle(self, *args, **options):
        flickr = Flickr(*settings.ARCHIVES_FLICKR_CREDENTIALS)

        store = redis.StrictRedis(**settings.PROLOGIN_UTILITY_REDIS_STORE)
        pipe = store.pipeline()

        tree = flickr.collection_tree()

        def by_title(node):
            data = {}
            for id, n in node.items():
                n = n.copy()
                if 'children' in n:
                    n['children'] = by_title(n['children'])
                data[n['title']] = n
            return data

        tree_by_title = by_title(tree)

        for archive in sorted(archives.models.Archive.all_archives()):
            collection = tree_by_title.get(str(archive))

            # drop everything
            count_key = archive.flickr_photo_count_key
            cover_photo_url_key = archive.flickr_cover_photo_url_key
            collection_url_key = archive.flickr_collection_url_key
            pipe.delete(count_key)
            pipe.delete(cover_photo_url_key)
            pipe.delete(collection_url_key)

            self.stdout.write(str(archive))

            if not collection:
                self.stderr.write("\tno Flickr collection")
                continue

            pipe.set(collection_url_key, collection['url'])

            # cover is collection mosaic by default
            cover_url = collection['iconlarge']

            photo_count = 0

            for album in collection['children'].values():
                if album['type'] != 'set':
                    continue

                album_id = album['id']
                album_info = flickr.album_info(album_id)
                # public photos only
                photos = list(flickr.photos(album_id, privacy_filter=1))
                photo_count += len(photos)

                # got final album, use its cover instead of collection mosaic
                if album['title'].strip() == FINAL_NAME.format(archive.year):
                    cover_url = album_info['cover']

            pipe.set(count_key, photo_count)
            pipe.set(cover_photo_url_key, cover_url)
            self.stdout.write("\t{} photos".format(photo_count))
            self.stdout.write("\tcover photo: {}".format(cover_url))

        # execute redis commands atomically
        pipe.execute()
