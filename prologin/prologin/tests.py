import contextlib
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from django.test import RequestFactory, TestCase
from django.test.client import Client
from django.utils import timezone

import contest.models
import team.models


class WithContestantMixin:
    def _contribute(self):
        super()._contribute()
        self.contestant = self.create_user(
            'contestant', 'contestant@example.com',
            first_name="Joseph", last_name="Marchand", phone='0642424242')


class WithStaffUserMixin:
    def _contribute(self):
        super()._contribute()
        self.staff_user = self.create_user(
            'staffer', 'staff@example.com',
            is_staff=True)


class WithOrgaUserMixin:
    def _contribute(self):
        super()._contribute()
        self.orga_user = self.create_user('organizer', 'organizer@example.com')

        self.orga_team_member = team.models.TeamMember(
            user=self.orga_user,
            year=self.edition_year,
            role_code=team.models.Role.president.name)
        self.orga_team_member.save()


class WithSuperUserMixin:
    def _contribute(self):
        super()._contribute()
        self.super_user = self.create_user(
            'superuser', 'superuser@example.com',
            is_staff=True, is_superuser=True)


class ProloginTestCase(TestCase):
    """Base class for prologin.org test cases.

    Sets up a decent environment with required database entries as well as few
    test users.
    """
    edition_year = settings.PROLOGIN_EDITION

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        self._contribute()

    def _contribute(self):
        self.edition = contest.models.Edition(
            year=settings.PROLOGIN_EDITION,
            date_begin=timezone.now(),
            date_end=timezone.now())
        self.edition.save()

        self.final_event = contest.models.Event(
            edition=self.edition,
            type=contest.models.Event.Type.final.value)
        self.final_event.save()

    @staticmethod
    def create_user(username, email, password='password', *args, **kwargs):
        user = get_user_model().objects.create_user(
            username, email, password, *args, **kwargs)
        # Keep the original password for convenience.
        user.original_password = password
        return user

    def client_login(self, user):
        return self.client.login(
            username=user.username,
            password=user.original_password)

    @contextlib.contextmanager
    def user_login(self, user):
        yield self.client_login(user)
        self.client.logout()

    def assertValidResponse(self, response):
        self.assertIsInstance(response, HttpResponse)
        code = response.status_code
        self.assertTrue(200 <= code < 300, msg="HTTP response should be valid but is {} {}".format(code, response.reason_phrase))

    def assertInvalidResponse(self, response):
        self.assertIsInstance(response, HttpResponse)
        code = response.status_code
        self.assertFalse(200 <= code < 300, msg="HTTP response should be erroneous but is {} {}".format(code, response.reason_phrase))

    def assertResponseCode(self, response, code):
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, code, msg="HTTP response should be {} but is {} {}".format(code, response.status_code, response.reason_phrase))
