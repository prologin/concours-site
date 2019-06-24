# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.apps import AppConfig

class ForumConfig(AppConfig):
    name = 'forum'
    verbose_name = 'Forum'

    def ready(self):
        import forum.signals
