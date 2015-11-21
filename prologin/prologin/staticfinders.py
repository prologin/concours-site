import glob
import os

from django.contrib.staticfiles.finders import BaseFinder
from django.contrib.staticfiles.utils import matches_patterns
from django.core.files.storage import FileSystemStorage


class PatternStaticFinder(BaseFinder):
    """Pattern-based static finder with optional prefix"""

    prefix = ''
    root = ''
    patterns = ()

    def find(self, path, all=False):
        if not self.patterns:
            return []
        if not path.startswith(self.prefix):
            return []
        path = path[len(self.prefix):]
        if not matches_patterns(path, self.patterns):
            return []
        abs_path = os.path.join(self.root, path.lstrip(os.path.sep))
        if os.path.exists(abs_path):
            return [abs_path] if all else abs_path
        return []

    def list(self, ignore_patterns):
        storage = FileSystemStorage(location=self.root)
        storage.prefix = self.prefix

        for pattern in self.patterns:
            for f in glob.glob(os.path.join(self.root, pattern.lstrip(os.path.sep))):
                if matches_patterns(f, ignore_patterns):
                    continue
                yield os.path.relpath(f, self.root), storage
