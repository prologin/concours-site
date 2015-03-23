from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db import connections
import logging

logger = logging.getLogger('prologin.backends')


class ModelBackendWithLegacy(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        user = super().authenticate(username, password, **kwargs)
        if user is not None:
            return user

        # Failed authentication with normal DB
        # Let's see if user is in legacy
        logger.info("User `%s` failed to connect; checking for legacy password", username)
        mysql = connections['mysql_legacy']
        with mysql.cursor() as cursor:
            cursor.execute("SELECT uid FROM users WHERE status = 1 AND name = %s AND pass = MD5(%s)", [
                username, password
            ])
            legacy = cursor.fetchone()
            if legacy is not None:
                user = get_user_model().objects.get(pk=legacy[0])
                assert user.username.lower() == username.lower()
                user.set_password(password)
                user.save()
                logger.info("User `%s` was found in legacy; password updated", username)
                return user
        # else return None, that's a real auth failure