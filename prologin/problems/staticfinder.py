import glob
import os
import os.path

from django.conf import settings
from django.contrib.staticfiles.finders import BaseFinder
from django.contrib.staticfiles.utils import matches_patterns
from django.core.files.storage import FileSystemStorage

class TrainingStaticFinder(BaseFinder):
    """Finds the problems static files"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pattern = '/*/*/static/*'

    def find(self, path, all=False):
        root = settings.TRAINING_PROBLEM_REPOSITORY_PATH

        prefix = 'problems'
        if not path.startswith(prefix):
            return []
        path = path[len(prefix):]
        if not matches_patterns(path, [self.pattern]):
            return []
        abpath = root + path
        if os.path.exists(abpath):
            return [abpath] if all else abpath
        return []

    def list(self, ignore_patterns):
        root = settings.TRAINING_PROBLEM_REPOSITORY_PATH
        storage = FileSystemStorage(location=root)
        storage.prefix = "problems"

        for f in glob.glob(root + self.pattern):
            if matches_patterns(f, ignore_patterns):
                continue
            yield os.path.relpath(f, root), storage
