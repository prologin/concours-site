from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from prologin.tests import Validator
from django.conf import settings

class TeamTest(TestCase):
    def setUp(self):
        self.validator = Validator()
        self.client = Client()

    def test_html(self):
        """
        Tests the HTML's compliance with the W3C standards.
        """
        response = self.client.get(reverse('home'))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True)

    def test_css(self):
        """
        Tests the CSS' compliance with the W3C standards.
        """
        path = settings.SITE_ROOT + 'prologin/static/prologin.css'
        css = open(path, 'r').read()
        valid = self.validator.checkCSS(css)
        self.assertEqual(valid, True)
