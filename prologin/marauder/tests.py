from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

import json

import marauder.api_views
import marauder.models
import marauder.views
from prologin import tests
from prologin.middleware import ContestMiddleware


class ReportingTestCase(tests.WithContestantMixin, tests.WithOrgaUserMixin, tests.ProloginTestCase):
    def make_request(self, data=None):
        if data is None:
            data = {}
        request = self.factory.post(
            reverse('marauder:api:report'),
            content_type='text/json',
            data=json.dumps(data))
        # RequestFactory does not support middlewares; apply it manually
        ContestMiddleware().process_request(request)
        return request

    def test_authorization(self):
        """Tests if a non-team member can get a profile."""
        # No user
        request = self.make_request()
        request.user = AnonymousUser()
        self.assertInvalidResponse(marauder.api_views.ApiReportView.as_view()(request))

        # Non-team user
        request = self.make_request()
        request.user = self.contestant
        self.assertInvalidResponse(marauder.api_views.ApiReportView.as_view()(request))

        # Team user
        request = self.make_request()
        request.user = self.orga_user
        self.assertValidResponse(marauder.api_views.ApiReportView.as_view()(request))

    def test_profile_creation(self):
        """Tests whether a profile gets created on first access."""
        self.assertFalse(marauder.models.UserProfile.objects.filter(
            user=self.orga_user))

        request = self.make_request()
        request.user = self.orga_user
        self.assertValidResponse(marauder.api_views.ApiReportView.as_view()(request))

        self.assertTrue(marauder.models.UserProfile.objects.filter(
            user=self.orga_user))

    def test_in_area(self):
        """Tests whether data gets stored when in area."""
        request = self.make_request({'in_area': True,
                                     'lat': 42,
                                     'lon': 1337,
                                     'gcm': {'app_id': 'test',
                                             'token': 'TOK'}})
        request.user = self.orga_user
        response = marauder.api_views.ApiReportView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        profile = marauder.models.UserProfile.objects.get(user=self.orga_user)
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
        request.user = self.orga_user
        response = marauder.api_views.ApiReportView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        profile = marauder.models.UserProfile.objects.get(user=self.orga_user)
        self.assertFalse(profile.in_area)
        self.assertEqual(profile.lat, 0)
        self.assertEqual(profile.lon, 0)
        self.assertEqual(profile.gcm_app_id, 'test')
        self.assertEqual(profile.gcm_token, 'TOK')
