import hashlib
import requests


class Flickr:
    API_ENDPOINT = 'https://api.flickr.com/services/rest/'

    def __init__(self, user_id, api_key, secret):
        self.user_id = user_id
        self.api_key = api_key
        self.secret = secret
        self.session = requests.Session()

    def _request(self, method, paginated=None, **kwargs):
        def sign(attrs):
            payload = self.secret + ''.join('{}{}'.format(k, v) for k, v in sorted(attrs.items()) if k != 'api_sig')
            return hashlib.md5(payload.encode('utf8')).hexdigest()

        attrs = {}
        attrs.update(kwargs)
        attrs['method'] = method
        attrs['api_key'] = self.api_key
        attrs['user_id'] = self.user_id
        attrs['format'] = 'json'
        attrs['nojsoncallback'] = '1'
        attrs['page'] = 1
        attrs['api_sig'] = sign(attrs)
        response = self.session.get(self.API_ENDPOINT, params=attrs).json()
        if paginated:
            root_key, objects_key = paginated
            yield from response[root_key][objects_key]
            pages = response[root_key]['pages']
            if pages > 1:
                for page in range(2, pages + 1):
                    attrs['page'] = page
                    attrs['api_sig'] = sign(attrs)
                    yield from self.session.get(self.API_ENDPOINT, params=attrs).json()[root_key][objects_key]
        else:
            return response

    def albums(self, **kwargs):
        return self._request('flickr.photosets.getList',
                             paginated=('photosets', 'photoset'),
                             **kwargs)

    def photos(self, album_id, extras='url_sq,url_t,url_s,url_m,url_o', **kwargs):
        return self._request('flickr.photosets.getPhotos',
                             photoset_id=album_id,
                             paginated=('photoset', 'photo'),
                             extras=extras,
                             **kwargs)
