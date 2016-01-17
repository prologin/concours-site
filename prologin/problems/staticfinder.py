from django.conf import settings

from prologin.staticfinders import PatternStaticFinder


class ProblemsStaticFinder(PatternStaticFinder):
    """Finds the problems static files"""

    root = settings.PROBLEMS_REPOSITORY_PATH
    prefix = settings.PROBLEMS_REPOSITORY_STATIC_PREFIX
    patterns = ('/*/*/static/*',)
