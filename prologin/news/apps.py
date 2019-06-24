# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.apps import AppConfig
from django.urls import reverse


class NewsConfig(AppConfig):
    name = 'news'
    verbose_name = 'News'

    def ready(self):
        # Terrible monkey patching to use our own author URL instead of
        # built-in zinnia profile. This is required because zinnia uses the
        # username in the URL but our username authorized charset is more
        # flexible than Django default. We allow eg. a quote in the username
        # (eg. "M'vy"), but zinnia does not include these chars in their
        # URL regexp. So this kind of usernames triggers a reverse lookup
        # exception.
        from zinnia.models.author import Author

        def get_absolute_url(self):
            return reverse('users:profile', args=[self.pk])

        Author.get_absolute_url = get_absolute_url
