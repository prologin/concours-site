from django.core.urlresolvers import reverse

import prologin.tests


class UsersTest(prologin.tests.ProloginTestCase):
    def test_http_response(self):
        """
        Tests the HTTP status codes.
        """
        response = self.client.get(reverse('users:profile',
                                           args=[self.contestant.id]))
        self.assertEqual(response.status_code, 200,
                         'invalid HTTP status code for users:profile')

        response = self.client.get(reverse('users:profile', args=(4269, )))
        self.assertEqual(response.status_code, 404,
                         'invalid HTTP status code for users:profile')

        response = self.client.get(reverse('users:edit',
                                           args=[self.contestant.id]))
        self.assertEqual(response.status_code, 403,
                         'invalid HTTP status code for users:edit (no user)')

        self.client_login(self.contestant)
        response = self.client.get(reverse('users:edit',
                                           args=[self.contestant.id]))
        self.assertEqual(
            response.status_code, 200,
            'invalid HTTP status code for users:edit (with a valid user)')
        self.client.logout()

        self.client_login(self.organizer)
        response = self.client.get(reverse('users:edit',
                                           args=[self.contestant.id]))
        self.assertEqual(
            response.status_code, 403,
            'invalid HTTP status code for users:edit (with a invalid user)')
        self.client.logout()

    def test_html(self):
        """
        Tests the HTML's compliance with the W3C standards.
        """
        response = self.client.get(reverse('users:profile',
                                           args=[self.contestant.id]))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True,
                         'invalid HTML for users:profile (not connected)')

        self.client_login(self.contestant)
        response = self.client.get(reverse('users:edit',
                                           args=[self.contestant.id]))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True, 'invalid HTML for users:profile')

        # TODO: broken
        #response = self.client.get(reverse('users:profile',
        #                                   args=[self.contestant.id]))
        #valid = self.validator.checkHTML(response.content)
        #self.assertEqual(valid, True,
        #                 'invalid HTML for users:profile (connected)')
        #self.client.logout()

        # Erk, the captcha breaks everything :x
        # response = self.client.get(reverse('users:register'))
        # valid = self.validator.checkHTML(response.content)
        # self.assertEqual(valid, True, 'invalid HTML for users:register')

        # TODO: broken
        #response = self.client.get(reverse('users:login'))
        #valid = self.validator.checkHTML(response.content)
        #self.assertEqual(valid, True, 'invalid HTML for users:login')
