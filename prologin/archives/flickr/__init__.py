import hashlib
import requests


class Flickr:
    API_ENDPOINT = 'https://api.flickr.com/services/rest/'
    PHOTO_FORMAT = 'format'

    def __init__(self, user_id, api_key, secret):
        self.user_id = user_id
        self.api_key = api_key
        self.secret = secret
        self.session = requests.Session()

    def _sign(self, attrs):
        payload = self.secret + ''.join('{}{}'.format(k, v) for k, v in sorted(attrs.items()) if k != 'api_sig')
        return hashlib.md5(payload.encode('utf8')).hexdigest()

    def _attrs(self, method, kwargs):
        attrs = {}
        attrs.update(kwargs)
        attrs['method'] = method
        attrs['api_key'] = self.api_key
        attrs['user_id'] = self.user_id
        attrs['format'] = 'json'
        attrs['nojsoncallback'] = '1'
        attrs['page'] = 1
        return attrs

    def _request(self, method, **kwargs):
        attrs = self._attrs(method, kwargs)
        attrs['api_sig'] = self._sign(attrs)
        return self.session.get(self.API_ENDPOINT, params=attrs).json()

    def _paginated_request(self, method, paginated, **kwargs):
        root_key, objects_key = paginated
        attrs = self._attrs(method, kwargs)
        attrs['api_sig'] = self._sign(attrs)
        response = self.session.get(self.API_ENDPOINT, params=attrs).json()
        yield from response[root_key][objects_key]
        pages = response[root_key]['pages']
        if pages <= 1:
            return
        for page in range(2, pages + 1):
            attrs['page'] = page
            attrs['api_sig'] = self._sign(attrs)
            yield from self.session.get(self.API_ENDPOINT, params=attrs).json()[root_key][objects_key]

    @classmethod
    def _photo_url(cls, farm, server, id, secret):
        return 'https://farm{}.staticflickr.com/{}/{}_{}_{{{}}}.jpg'.format(farm, server, id, secret, cls.PHOTO_FORMAT)

    @classmethod
    def _add_cover(cls, album):
        album['cover'] = cls._photo_url(album['farm'], album['server'], album['primary'], album['secret'])
        return album

    @classmethod
    def photo_url_format(cls, url, format):
        return url.format(**{cls.PHOTO_FORMAT: format})

    def collection_tree(self):
        collections = self._request('flickr.collections.getTree')['collections']['collection']
        data = {}

        def explore(data, node, type):
            id = node['id']
            data[id] = subdata = node
            subdata['type'] = type
            if type == 'collection':
                url = 'https://www.flickr.com/photos/{}/collections/{}'.format(self.user_id, id.split('-', 1)[1])
            elif type == 'set':
                url = 'https://www.flickr.com/photos/{}/sets/{}/'.format(self.user_id, id)
            else:
                raise TypeError("unknown type {}".format(type))
            subdata['url'] = url
            subdata['children'] = children = {}
            if 'collection' in node:
                for collection in node.pop('collection'):
                    explore(children, collection, 'collection')
            elif 'set' in node:
                for set in node.pop('set'):
                    explore(children, set, 'set')

        for collection in collections:
            explore(data, collection, 'collection')

        return data

    def album_info(self, album_id):
        album = self._request('flickr.photosets.getInfo', photoset_id=album_id)['photoset']
        return self._add_cover(album)

    def albums(self, **kwargs):
        albums = self._paginated_request('flickr.photosets.getList', ('photosets', 'photoset'), **kwargs)
        return (self._add_cover(album) for album in albums)

    def photos(self, album_id, extras='url_sq,url_t,url_s,url_m,url_o', **kwargs):
        return self._paginated_request('flickr.photosets.getPhotos', ('photoset', 'photo'),
                                       photoset_id=album_id, extras=extras, **kwargs)
