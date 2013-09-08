from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from users.models import ProloginUser
from prologin.tests import Validator

class UsersTest(TestCase):
    def setUp(self):
        self.validator = Validator()
        self.client = Client()
        self.pu = ProloginUser()
        self.user_profile = self.pu.register('toto', 'toto1@example.org', 'password', True)

    def test_register(self):
        """
        Tests the user registration.
        """
        self.assertRaises(ValueError, self.pu.register, 'toto', 'toto2@example.org', 'password', True)
        self.assertRaises(ValueError, self.pu.register, 'Toto', 'toto3@example.org', 'password', True)
        self.assertRaises(ValueError, self.pu.register, 'töto', 'toto4@example.org', 'password', True)

    def test_short_name(self):
        """
        Tests the user short name.
        """
        self.assertEqual(self.user_profile.short_name, 'toto')
        
        p = self.pu.register('è_é -', 'test@example.org', 'password', True)
        self.assertEqual(p.short_name, 'e_e_-')

    def test_http_response(self):
        """
        Tests the HTTP response.
        """
        response = self.client.get(reverse('users:profile', args=(self.user_profile.short_name,)))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('users:profile', args=(self.user_profile.user.id,)))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('users:profile', args=(4269,)))
        self.assertEqual(response.status_code, 404)

    def test_html(self):
        """
        Tests the HTML's compliance with the W3C standards.
        """        
        response = self.client.get(reverse('users:profile', args=(self.user_profile.short_name,)))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True)
