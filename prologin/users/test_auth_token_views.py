import datetime
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from prologin.settings.common import AuthTokenClient
from users.models import ProloginUser, AuthToken

CLIENT_SECRET = 'my-super-secret-string'
CLIENT_REDIRECT_URL = 'https://example.org/auth/callback'


def set_datetime(*args):
    return patch.object(
        timezone, 'now', return_value=make_aware(datetime.datetime(*args)))


@override_settings(
    AUTH_TOKEN_CLIENTS={
        'test': AuthTokenClient(CLIENT_SECRET, CLIENT_REDIRECT_URL)
    },
    AUTH_TOKEN_ACCESS_EXPIRATION=datetime.timedelta(hours=1),
    AUTH_TOKEN_REFRESH_EXPIRATION=datetime.timedelta(hours=6))
class TestAuthTokenViews(TestCase):
    def setUp(self):
        self.user = ProloginUser.objects.create(
            username="user",
            email="user@mail",
            first_name="jean",
            last_name="dup")
        self.client = Client(enforce_csrf_checks=True)

    def json(self, url, data, **kwargs):
        return self.client.post(
            url, content_type='application/json', data=data, **kwargs)

    def test_authorize_anonymous(self):
        # login redirect
        r = self.client.get('/user/auth/authorize')
        self.assertEqual(r.status_code, 302)

    def test_authorize_no_client(self):
        self.client.force_login(user=self.user)
        r = self.client.get('/user/auth/authorize')
        self.assertEqual(r.status_code, 400)

    def test_authorize_unknown_client(self):
        self.client.force_login(user=self.user)
        r = self.client.get('/user/auth/authorize?client_id=garbage')
        self.assertEqual(r.status_code, 400)

    def test_authorize_no_state(self):
        self.client.force_login(user=self.user)
        r = self.client.get('/user/auth/authorize?client_id=test')
        self.assertEqual(r.status_code, 400)

    def test_authorize_works(self):
        self.client.force_login(user=self.user)
        result = self.client.get(
            '/user/auth/authorize?client_id=test&state=foo')
        self.assertEqual(result.status_code, 302)
        self.assertEqual(1, AuthToken.objects.count())
        token = AuthToken.objects.get()
        self.assertIn('state=foo', result.url)
        self.assertIn('code=' + token.code, result.url)
        self.assertTrue(result.url.startswith(CLIENT_REDIRECT_URL + '?'))

    def test_token_access_bad_method(self):
        self.assertEqual(self.client.get('/user/auth/token').status_code, 405)

    def test_token_access_no_code(self):
        self.assertEqual(self.client.post('/user/auth/token').status_code, 400)

    def test_token_access_garbage_body(self):
        r = self.client.post(
            '/user/auth/token',
            content_type='application/json',
            data=b"garbage")
        self.assertEqual(r.status_code, 400)

    def test_token_access_no_client(self):
        r = self.json('/user/auth/token', data={'code': 'foo'})
        self.assertEqual(r.status_code, 400)

    def test_token_access_unknown_client(self):
        r = self.json('/user/auth/token', data={'client_id': 'garbage'})
        self.assertEqual(r.status_code, 400)

    def test_token_access_bad_client_secret(self):
        r = self.json(
            '/user/auth/token',
            data={
                'client_id': 'test',
                'client_secret': 'garbage',
            })

        self.assertEqual(r.status_code, 400)

    def test_token_access_unknown_code(self):
        r = self.json(
            '/user/auth/token',
            data={
                'client_id': 'test',
                'client_secret': CLIENT_SECRET,
                'code': 'garbage',
            })
        self.assertEqual(r.status_code, 400)

    def test_token_access_expired(self):
        with set_datetime(2019, 1, 1, 10, 0):
            token = AuthToken.generate('test', self.user)
            token.save()

        # One minute after expiration.
        with set_datetime(2019, 1, 1, 11, 1):
            r = self.json(
                '/user/auth/token',
                data={
                    'client_id': 'test',
                    'client_secret': CLIENT_SECRET,
                    'code': token.code,
                })

        self.assertEqual(r.status_code, 400)

    def test_token_access_works(self):
        with set_datetime(2019, 1, 1, 10, 0):
            token = AuthToken.generate('test', self.user)
            token.save()

        token = AuthToken.objects.get()
        self.assertNotEqual(token.code, None)

        # One minute before expiration.
        with set_datetime(2019, 1, 1, 10, 59):
            r = self.json(
                '/user/auth/token',
                data={
                    'client_id': 'test',
                    'client_secret': CLIENT_SECRET,
                    'code': token.code,
                })

        self.assertEqual(r.status_code, 200)
        json = r.json()
        self.assertEqual(json['refresh_token'], token.refresh_token)
        self.assertEqual(json['user']['pk'], self.user.pk)
        self.assertEqual(json['user']['username'], self.user.username)
        self.assertEqual(json['user']['is_staff'], self.user.is_staff)
        expires = parse_datetime(json['expires'])
        self.assertTrue(timezone.is_aware(token.expiration_datetime()))
        self.assertTrue(timezone.is_aware(expires))
        self.assertEqual(expires, token.expiration_datetime())

    def test_token_access_works_one_time(self):
        with set_datetime(2019, 1, 1, 10, 0):
            token = AuthToken.generate('test', self.user)
            token.save()

        # One minute before expiration.
        with set_datetime(2019, 1, 1, 10, 59):
            r = self.json(
                '/user/auth/token',
                data={
                    'client_id': 'test',
                    'client_secret': CLIENT_SECRET,
                    'code': token.code,
                })
            # OK the first time.
            self.assertEqual(r.status_code, 200)

            r = self.json(
                '/user/auth/token',
                data={
                    'client_id': 'test',
                    'client_secret': CLIENT_SECRET,
                    'code': token.code,
                })
            # Error the other times.
            self.assertEqual(r.status_code, 400)

    def test_token_refresh_no_token(self):
        r = self.json(
            '/user/auth/refresh',
            data={
                'client_id': 'test',
                'client_secret': CLIENT_SECRET,
            })
        self.assertEqual(r.status_code, 400)

    def test_token_refresh_unknown_token(self):
        r = self.json(
            '/user/auth/refresh',
            data={
                'client_id': 'test',
                'client_secret': CLIENT_SECRET,
                'refresh_token': 'garbage',
            })
        self.assertEqual(r.status_code, 400)

    def test_token_refresh_expired(self):
        with set_datetime(2019, 1, 1, 10, 0):
            token = AuthToken.generate('test', self.user)
            token.save()

        # One minute after expiration.
        with set_datetime(2019, 1, 1, 16, 1):
            r = self.json(
                '/user/auth/refresh',
                data={
                    'client_id': 'test',
                    'client_secret': CLIENT_SECRET,
                    'refresh_token': token.refresh_token,
                })

        self.assertEqual(r.status_code, 400)

    def test_token_refresh_works(self):
        with set_datetime(2019, 1, 1, 10, 0):
            token = AuthToken.generate('test', self.user)
            token.save()

        # One minute before expiration.
        with set_datetime(2019, 1, 1, 15, 59):
            r = self.json(
                '/user/auth/refresh',
                data={
                    'client_id': 'test',
                    'client_secret': CLIENT_SECRET,
                    'refresh_token': token.refresh_token,
                })

        self.assertEqual(r.status_code, 200)
        json = r.json()
        self.assertEqual(json['user']['pk'], self.user.pk)
        self.assertEqual(json['user']['username'], self.user.username)
        self.assertEqual(json['user']['is_staff'], self.user.is_staff)
        expires = parse_datetime(json['expires'])
        self.assertTrue(timezone.is_aware(token.expiration_datetime()))
        self.assertTrue(timezone.is_aware(expires))
        self.assertEqual(expires, token.expiration_datetime())

    def test_expired_tokens_garbage_collected(self):
        with set_datetime(2019, 1, 1, 10, 0):
            token = AuthToken.generate('test', self.user)
            token.save()
            self.assertEqual(AuthToken.objects.count(), 1)

        with set_datetime(2019, 1, 1, 15, 59):
            # Not expired.
            AuthToken.garbage_collect()
            self.assertEqual(AuthToken.objects.count(), 1)

        with set_datetime(2019, 1, 1, 16, 1):
            # Expired.
            AuthToken.garbage_collect()
            self.assertEqual(AuthToken.objects.count(), 0)

    def test_invalid_tokens_garbage_collected(self):
        with set_datetime(2019, 1, 1, 10, 0):
            token = AuthToken.generate('test', self.user)
            token.save()
            self.assertEqual(AuthToken.objects.count(), 1)

        with set_datetime(2019, 1, 1, 15, 59):
            # Not invalid.
            AuthToken.garbage_collect()
            self.assertEqual(AuthToken.objects.count(), 1)

            # Invalid.
            self.user.is_active = False
            self.user.save()
            AuthToken.garbage_collect()
            self.assertEqual(AuthToken.objects.count(), 0)
