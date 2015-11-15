from django.conf import settings

from prologin.staticfinders import PatternStaticFinder


class TrainingStaticFinder(PatternStaticFinder):
    """Finds the problems static files"""

    root = settings.TRAINING_PROBLEM_REPOSITORY_PATH
    prefix = settings.TRAINING_PROBLEM_REPOSITORY_STATIC_PREFIX
    patterns = ('/*/*/static/*',)
