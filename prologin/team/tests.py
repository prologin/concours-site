from django.conf import settings
from django.core.urlresolvers import reverse

import prologin.tests


class TeamTest(prologin.tests.ProloginTestCase):
    def test_http_response(self):
        """
        Tests the HTTP response.
        """
        response = self.client.get(reverse('team:year', args=(13, )))
        self.assertEqual(response.status_code, 404,
                         'invalid HTTP status code for team:year')

        response = self.client.get(reverse('team:year',
                                           args=(settings.PROLOGIN_EDITION, )))
        self.assertEqual(response.status_code, 200,
                         'invalid HTTP status code for team:year')

    def test_html(self):
        """
        Tests the HTML's compliance with the W3C standards.
        """
        response = self.client.get(reverse('team:year', args=(2013, )))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True, 'invalid HTML for team:year')
