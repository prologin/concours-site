from django.conf import settings

from prologin.staticfinders import PatternStaticFinder


class ArchivesStaticFinder(PatternStaticFinder):
    """Finds the archives static files"""

    root = settings.GCC_REPOSITORY_PATH
    prefix = settings.GCC_REPOSITORY_STATIC_PREFIX
    patterns = (
        '/*/poster.*.jpg',
    )
