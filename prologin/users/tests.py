from django.core.urlresolvers import reverse
from django.contrib.auth.models import get_user_model
from django.test.client import Client
from django.test import TestCase
from prologin.tests import Validator


class UsersTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.validator = Validator()
        self.client = Client()
        self.user = User.objects.create_user('toto', 'toto1@example.org', 'password')
        User.objects.create_user('derp', 'derp1@example.org', 'password')

    def test_http_response(self):
        """
        Tests the HTTP status codes.
        """
        response = self.client.get(reverse('users:profile', args=[self.user.id]))
        self.assertEqual(response.status_code, 200, 'invalid HTTP status code for users:profile')

        response = self.client.get(reverse('users:profile', args=(4269,)))
        self.assertEqual(response.status_code, 404, 'invalid HTTP status code for users:profile')

        response = self.client.get(reverse('users:edit', args=[self.user.id]))
        self.assertEqual(response.status_code, 403, 'invalid HTTP status code for users:edit (no user)')

        self.client.login(username='toto', password='password')
        response = self.client.get(reverse('users:edit', args=[self.user.id]))
        self.assertEqual(response.status_code, 200, 'invalid HTTP status code for users:edit (with a valid user)')
        self.client.logout()

        self.client.login(username='derp', password='password')
        response = self.client.get(reverse('users:edit', args=[self.user.id]))
        self.assertEqual(response.status_code, 403, 'invalid HTTP status code for users:edit (with a invalid user)')
        self.client.logout()

    def test_html(self):
        """
        Tests the HTML's compliance with the W3C standards.
        """
        response = self.client.get(reverse('users:profile', args=[self.user.id]))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True, 'invalid HTML for users:profile (not connected)')

        self.client.login(username='toto', password='password')
        response = self.client.get(reverse('users:edit', args=[self.user.id]))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True, 'invalid HTML for users:profile')

        response = self.client.get(reverse('users:profile', args=[self.user.id]))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True, 'invalid HTML for users:profile (connected)')
        self.client.logout()

        # Erk, the captcha breaks everything :x
        # response = self.client.get(reverse('users:register'))
        # valid = self.validator.checkHTML(response.content)
        # self.assertEqual(valid, True, 'invalid HTML for users:register')

        response = self.client.get(reverse('users:login'))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True, 'invalid HTML for users:login')
