from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.test.client import Client
from django.utils import timezone

import http.client
import urllib.parse
import time
import re

import contest.models
import team.models


class ProloginTestCase(TestCase):
    """Base class for prologin.org test cases.

    Sets up a decent environment with required database entries as well as few
    test users.
    """

    def setUp(self):
        self.validator = Validator()
        self.client = Client()
        self.factory = RequestFactory()

        self._make_edition()
        self._make_users()

    def _make_users(self):
        self.contestant = self.create_user(
            'contestant', 'contestant@example.com', 'password')
        self.organizer = self.create_user('organizer', 'organizer@example.com',
                                          'password')

        self.organizer_tm = team.models.TeamMember()
        self.organizer_tm.user = self.organizer
        self.organizer_tm.role_code = team.models.Role.president.name
        self.organizer_tm.year = settings.PROLOGIN_EDITION
        self.organizer_tm.save()

    def _make_edition(self):
        self.edition = contest.models.Edition()
        self.edition.year = settings.PROLOGIN_EDITION
        self.edition.date_begin = timezone.now()
        self.edition.date_end = timezone.now()
        self.edition.save()

        self.finals = contest.models.Event()
        self.finals.edition = self.edition
        self.finals.type = contest.models.Event.Type.final.value
        self.finals.save()

    def create_user(self, username, email, password, *args, **kwargs):
        user = get_user_model().objects.create_user(username, email, password,
                                                    *args, **kwargs)
        # Keep the original password for convenience.
        user.original_password = password
        return user

    def client_login(self, user):
        return self.client.login(username=user.username,
                                 password=user.original_password)


# TODO: Replace with a local validation library.
class Validator:
    def __init__(self):
        self.useragent = (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')

    def SOAPValidity(self, soap):
        # Why not using a lib?
        # 1. including dependencies only for unit testing sounds weird
        # 2. at this time, there's no good and maintained projects.
        pat = re.compile(r'^.*<m:validity>true</m:validity>.*$', re.M | re.I)
        return pat.search(soap) != None

    def wait(self):
        """Pause the script so it doesn't flood the W3C Validation Service.

        "Please be considerate in using this shared, free resource. Consider
        Installing your own instance of the validator for smooth and fast
        operation. Excessive use of the W3C Validation Service will be
        blocked."
        -- http://validator.w3.org/docs/api.html
        """
        time.sleep(1)

    def checkHTML(self, html):
        self.wait()
        conn = http.client.HTTPConnection('validator.w3.org')
        params = urllib.parse.urlencode({
            'fragment': html,
            'prefill': 0,
            'doctype': 'Inline',
            'prefill_doctype': 'html401',
            'group': 0,
            'output': 'soap12',
        })
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain,text/html,application/xhtml+xml,'
                      'application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': self.useragent,
        }
        conn.request('POST', '/check', params, headers)
        response = conn.getresponse()
        if response.status != 200:
            return False
        data = response.read()
        return self.SOAPValidity(str(data))

    def checkCSS(self, css):
        self.wait()
        conn = http.client.HTTPConnection('jigsaw.w3.org')
        params = urllib.parse.urlencode({
            'text': css,
            'profile': 'css3',
            'usermedium': 'all',
            'type': 'none',
            'warning': '1',
            'vextwarning': 'true',
            'lang': 'en',
            'output': 'soap12',
        })
        headers = {
            'Accept': 'text/plain,text/html,application/xhtml+xml,'
                      'application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': self.useragent,
        }
        conn.request('GET',
                     '/css-validator/validator?' + str(params),
                     headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            return False
        data = response.read()
        return self.SOAPValidity(str(data))
