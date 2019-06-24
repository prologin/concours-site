# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.conf import settings

from prologin.staticfinders import PatternStaticFinder


class ArchivesStaticFinder(PatternStaticFinder):
    """Finds the archives static files"""

    root = settings.ARCHIVES_REPOSITORY_PATH
    prefix = settings.ARCHIVES_REPOSITORY_STATIC_PREFIX
    patterns = (
        '/*/poster.*.jpg',
        '/*/questionnaire/*.pdf',
        '/*/demi-finales/sujet/*',
        '/*/finale/confs/*',
        '/*/finale/sujet/*',
        '/*/finale/xdm/*',
    )
