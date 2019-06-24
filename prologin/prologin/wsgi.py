# Copyright (C) <2013> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

"""
WSGI config for prologin project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prologin.settings.prod")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
