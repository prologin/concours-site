from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden

import json

import marauder.api_views
import marauder.models
import marauder.views
import prologin.tests


class ReportingTestCase(prologin.tests.ProloginTestCase):
    def make_request(self, data=None):
        if data is None:
            data = {}
        return self.factory.post(
            reverse('marauder:api:report'),
            content_type='text/json',
            data=json.dumps(data))

    def test_authorization(self):
        """Tests if a non-team member can get a profile."""
        # No user
        request = self.make_request()
        request.user = AnonymousUser()
        response = marauder.api_views.report(request)
        self.assertEqual(response.status_code, 302)

        # Non-team user.
        request = self.make_request()
        request.user = self.contestant
        response = marauder.api_views.report(request)
        self.assertEqual(response.status_code, 403)

        # Team user.
        request = self.make_request()
        request.user = self.organizer
        response = marauder.api_views.report(request)
        self.assertEqual(response.status_code, 200)

    def test_profile_creation(self):
        """Tests whether a profile gets created on first access."""
        self.assertFalse(marauder.models.UserProfile.objects.filter(
            user=self.organizer))

        request = self.make_request()
        request.user = self.organizer
        response = marauder.api_views.report(request)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(marauder.models.UserProfile.objects.filter(
            user=self.organizer))

    def test_in_area(self):
        """Tests whether data gets stored when in area."""
        request = self.make_request({'in_area': True,
                                     'lat': 42,
                                     'lon': 1337,
                                     'gcm': {'app_id': 'test',
                                             'token': 'TOK'}})
        request.user = self.organizer
        response = marauder.api_views.report(request)
        self.assertEqual(response.status_code, 200)

        profile = marauder.models.UserProfile.objects.get(user=self.organizer)
        self.assertTrue(profile.in_area)
        self.assertEqual(profile.lat, 42)
        self.assertEqual(profile.lon, 1337)
        self.assertEqual(profile.gcm_app_id, 'test')
        self.assertEqual(profile.gcm_token, 'TOK')

    def test_out_of_area(self):
        """Tests whether non-loc data gets stored when out of area."""
        request = self.make_request({'in_area': False,
                                     'lat': 42,
                                     'lon': 1337,
                                     'gcm': {'app_id': 'test',
                                             'token': 'TOK'}})
        request.user = self.organizer
        response = marauder.api_views.report(request)
        self.assertEqual(response.status_code, 200)

        profile = marauder.models.UserProfile.objects.get(user=self.organizer)
        self.assertFalse(profile.in_area)
        self.assertEqual(profile.lat, 0)
        self.assertEqual(profile.lon, 0)
        self.assertEqual(profile.gcm_app_id, 'test')
        self.assertEqual(profile.gcm_token, 'TOK')
