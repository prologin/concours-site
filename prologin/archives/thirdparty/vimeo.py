from django.conf import settings
from django.utils.html import format_html
from vimeo import VimeoClient


class Vimeo:
    def __init__(self):
        key, secrets, token = settings.ARCHIVES_VIMEO_CREDENTIALS
        self.client = VimeoClient(token=token, key=key, secret=secrets)

    def _iter(self, method, url, *args, **kwargs):
        method = getattr(self.client, method)
        data = method(url, *args, **kwargs).json()
        yield from data['data']
        while True:
            next_url = data['paging']['next']
            if not next_url:
                break
            data = method(next_url).json()
            yield from data['data']

    def videos(self):
        def with_ids(video):
            # yeah, raw id is not included, what the fuck Vimeo?
            video['id'] = video['uri'].rsplit('/', 1)[-1]
            video['picture_id'] = video['pictures']['uri'].rsplit('/', 1)[-1]
            return video
        return (with_ids(video) for video in self._iter('get', '/me/videos'))

    @classmethod
    def video_cover_url(cls, id, size, fill=''):
        if isinstance(size, int):
            w = h = size
        else:
            w, h = size
        return 'https://i.vimeocdn.com/video/{id}_{w}x{h}.webp?r={fill}'.format(id=id, w=w, h=h, fill=fill)

    @classmethod
    def video_url(cls, video_id):
        return 'https://vimeo.com/{}'.format(video_id)

    @classmethod
    def video_embed_code(cls, video_id, width, height, portrait=False, byline=False, autoplay=False):
        return format_html('<iframe src="https://player.vimeo.com/video/{id}'
                           '?badge=0&portrait={p}&byline={bl}&autoplay={ap}" '
                           'width="{w}" height="{h}" frameborder="0" '
                           'webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>',
                           id=video_id, w=width, h=height, p=int(portrait), bl=int(byline), ap=int(autoplay))
