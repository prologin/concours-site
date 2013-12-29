from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from users.models import UserProfile
from prologin.tests import Validator

class UsersTest(TestCase):
    def setUp(self):
        self.validator = Validator()
        self.client = Client()
        self.user_profile = UserProfile.register('toto', 'toto1@example.org', 'password', True)

    def test_register_duplicate(self):
        """
        Check if it's impossible to register the same user two times.
        """
        self.assertRaises(ValueError, UserProfile.register, 'toto', 'toto2@example.org', 'password', True)
        self.assertRaises(ValueError, UserProfile.register, 'Toto', 'toto3@example.org', 'password', True)
        self.assertRaises(ValueError, UserProfile.register, 'töto', 'toto4@example.org', 'password', True)

    def test_slug(self):
        """
        Tests the user short name.
        """
        self.assertEqual(self.user_profile.slug, 'toto')
        
        p = UserProfile.register('è_é -', 'test@example.org', 'password', True)
        self.assertEqual(p.slug, 'e_e_-')

    def test_http_response(self):
        """
        Tests the HTTP response.
        """
        response = self.client.get(reverse('users:profile', args=(self.user_profile.slug,)))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('users:profile', args=(self.user_profile.user.id,)))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('users:profile', args=(4269,)))
        self.assertEqual(response.status_code, 404)

    def test_html(self):
        """
        Tests the HTML's compliance with the W3C standards.
        """        
        response = self.client.get(reverse('users:profile', args=(self.user_profile.slug,)))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True)

        response = self.client.get(reverse('users:register'))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True)
