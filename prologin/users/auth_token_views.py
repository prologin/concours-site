"""
A bunch of views implementing a bare-bones OAuth2 "Authorization code" provider.

Assumptions:
    Clients (third party apps) are registered by having an entry in
    settings.AUTH_TOKEN_CLIENTS of the form
    {'client id': AuthTokenClient('client secret', 'client callback URL')}

    Clients know their client id and client secret.

    Clients can persist a local version of their users and the associated
    refresh token string.

Protocol for logging in (client has no session):
    1. Client redirects user browser to
       //prologin.org/user/auth/authorize?client_id=<client id>&state=<state>
       with state a random string that is memorized (eg. in a cookie)

    2. User logs in on prologin.org (or is already logged in)

    3. User browser is redirected to the client callback URL, eg.
       //gcc.prologin.org/user/auth/callback?code=<random code>?state=<state>

    4. Client checks that <state> is the same as its request's and makes an
       internal POST request to
       //prologin.org/user/auth/token with the JSON payload:
       {"code": "<code>",
        "client_id": "<client id>",
        "client_secret": "<client secret>"}

    5. The successful response is a JSON payload:
       {"refresh_token": "<refresh token>", "user": <user object>}

       Client updates its user instance with <user object>
       alongside the refresh token.

Protocol for every authenticated client requests:
    6. Client makes an internal POST request to //prologin.org/user/auth/refresh
       with the JSON payload:
       {"refresh_token": "<refresh token>",
        "client_id": "<client id>",
        "client_secret": "<client secret>"}

    7. a. If the token is still valid (not too old and user is valid) then the
          response handling described in 5. applies.
       b. If the response is an error, the client should log out the user and
          redirect the user browser to the authorization flow described in 1.
"""

import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.crypto import constant_time_compare
from django.utils.http import urlencode
from django.views import View
from django.views.generic import RedirectView
from rules.contrib.views import PermissionRequiredMixin

from users.models import AuthToken


class AuthorizeView(PermissionRequiredMixin, RedirectView):
    permission_required = 'users.external-auth'
    client_id_query = 'client_id'
    state_query = 'state'

    def get_url(self, *args, **kwargs):
        initiator_name = self.request.GET.get(self.client_id_query)
        state = self.request.GET.get(self.state_query)

        if not state:
            raise ValueError("missing state")

        client = settings.AUTH_TOKEN_CLIENTS[initiator_name]

        auth_token = AuthToken.generate(initiator_name, self.request.user)
        auth_token.save()

        # Piggy-back on the view to do garbage collection.
        AuthToken.garbage_collect()

        return client.redirect_url + '?' + urlencode(
            {
                'code': auth_token.code,
                'state': state
            })

    def get(self, request, *args, **kwargs):
        try:
            self.url = self.get_url()
        except Exception:
            return HttpResponseBadRequest()
        return super().get(request, *args, **kwargs)


class TokenRetrievalMixin:
    client_id_param = 'client_id'
    client_secret_param = 'client_secret'

    def get_identifier(self, payload):
        raise NotImplementedError()

    def get_token(self, initiator_name, identifier):
        raise NotImplementedError()

    def on_success(self, auth_token):
        pass

    def post(self, request, *args, **kwargs):
        def error(reason):
            return HttpResponseBadRequest(json.dumps({"error": reason}))

        if request.content_type != 'application/json':
            return error("expected JSON payload")

        try:
            payload = json.loads(request.body.decode())
            client_id = payload[self.client_id_param]
            client_secret = payload[self.client_secret_param]
            identifier = self.get_identifier(payload)
        except Exception:
            return error("malformed JSON payload")

        try:
            client = settings.AUTH_TOKEN_CLIENTS[client_id]
        except KeyError:
            return error("unknown client")

        if not constant_time_compare(client.secret, client_secret):
            return error("invalid client secret")

        try:
            auth_token = self.get_token(client_id, identifier)
        except ObjectDoesNotExist:
            return error("token does not exist (may have expired)")
        except Exception as exc:
            return error(
                "unexpected error while retrieving token: {}".format(exc))

        self.on_success(auth_token)

        # Piggy-back on the view to do garbage collection.
        AuthToken.garbage_collect()

        return JsonResponse(auth_token.as_dict())


class AccessTokenView(TokenRetrievalMixin, View):
    def get_identifier(self, payload):
        return payload['code']

    def get_token(self, initiator_name, code):
        return AuthToken.verify_for_access(initiator_name, code)

    def on_success(self, auth_token):
        # Invalidate the one-time code.
        auth_token.mark_code_used()
        auth_token.save()


class RefreshTokenView(TokenRetrievalMixin, View):
    def get_identifier(self, payload):
        return payload['refresh_token']

    def get_token(self, initiator_name, refresh_token):
        return AuthToken.verify_for_refresh(initiator_name, refresh_token)
