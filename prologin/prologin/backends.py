# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
import hashlib
import logging

logger = logging.getLogger('prologin.backends')


class ModelBackendWithLegacy(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is not None:
            return user

        # Failed authentication with Django password
        # Check if user has a legacy password
        User = get_user_model()
        try:
            user = User.objects.get(username__iexact=username,
                                    legacy_md5_password=hashlib.md5(password.encode('utf-8')).hexdigest())
            user.set_password(password)
            # Empty out the legacy password (for security & progress stats purposes)
            user.legacy_md5_password = ''
            user.save()
            logger.info("User `%s` authenticated with legacy password; "
                        "Django password updated", username)
            return user
        except User.DoesNotExist:
            pass
