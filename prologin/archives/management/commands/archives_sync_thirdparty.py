# Copyright (C) <2017> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import redis
from django.conf import settings
from django.core.management import BaseCommand

import archives.models
from archives.thirdparty.flickr import Flickr
from archives.thirdparty.vimeo import Vimeo

FINAL_NAME = "{} Finale"


class Command(BaseCommand):
    help = "Synchronize Flickr and Vimeo data for archives into Redis"

    @staticmethod
    def flickr_collections_by_title(tree):
        def by_title(node):
            data = {}
            for id, n in node.items():
                n = n.copy()
                if 'children' in n:
                    n['children'] = by_title(n['children'])
                data[n['title']] = n
            return data
        return by_title(tree)

    @staticmethod
    def vimeo_videos_by_title(videos):
        return {video['name']: video for video in videos}

    def handle_flickr_collection(self, collections, archive):
        # drop everything
        self.pipe.delete(archive.photo_count_key)
        self.pipe.delete(archive.photo_cover_url_key)
        self.pipe.delete(archive.photo_collection_url_key)

        collection = collections.get(str(archive))
        if not collection:
            self.stderr.write("\tno Flickr collection")
            return

        self.pipe.set(archive.photo_collection_url_key, collection['url'])

        # cover is collection mosaic by default
        cover_url = collection['iconlarge']

        photo_count = 0

        for album in collection['children'].values():
            if album['type'] != 'set':
                continue

            album_id = album['id']
            album_info = self.flickr.album_info(album_id)
            # public photos only
            photos = list(self.flickr.photos(album_id, privacy_filter=1))
            photo_count += len(photos)

            # got final album, use its cover instead of collection mosaic
            if album['title'].strip() == FINAL_NAME.format(archive.year):
                cover_url = album_info['cover']

        self.pipe.set(archive.photo_count_key, photo_count)
        self.pipe.set(archive.photo_cover_url_key, cover_url)

        self.stdout.write("\t{} photos".format(photo_count))
        self.stdout.write("\tcover photo: {}".format(cover_url))

    def handle_vimeo_video(self, videos, archive):
        # drop everything
        self.pipe.delete(archive.video_id_key)
        self.pipe.delete(archive.video_picture_id_key)

        video = videos.get(str(archive))
        if not video:
            self.stderr.write("\tno Vimeo video")
            return

        self.pipe.set(archive.video_id_key, video['id'])
        self.pipe.set(archive.video_picture_id_key, video['picture_id'])
        self.stdout.write("\tvideo: {}".format(video['link']))

    def handle(self, *args, **options):
        store = redis.StrictRedis(**settings.PROLOGIN_UTILITY_REDIS_STORE)
        self.pipe = store.pipeline()

        self.flickr = Flickr()
        collections = self.flickr_collections_by_title(self.flickr.collection_tree())

        self.vimeo = Vimeo()
        videos = self.vimeo_videos_by_title(self.vimeo.videos())

        for archive in sorted(archives.models.Archive.all_archives()):
            self.stdout.write(str(archive))
            self.handle_flickr_collection(collections, archive)
            self.handle_vimeo_video(videos, archive)

        # execute all redis commands atomically
        self.pipe.execute()
