from django.template import VariableDoesNotExist, Variable
from django.utils.html import escape
import enum
import hashlib
import inspect
import os
import re
import string
import unicodedata
import uuid


def get_slug(name):
    name = unicodedata.normalize('NFKD', name.lower())
    name = ''.join(x for x in name if x in string.ascii_letters + string.digits + ' _-')
    name = re.sub(r'[^a-z0-9\-]', '_', name)
    return name


def real_value(var, context):
    """Return the real value based on the context."""
    if var is None:
        return None
    try:
        if not isinstance(var, Variable):
            var = Variable(var)
        real_var = var.resolve(context)
    except VariableDoesNotExist:
        real_var = str(var)
    return escape(real_var)


def upload_path(*base_path):
    """
    Generate upload path for a FileInput.
    `base_path`: folder path of where to put the files
    Examples:
        upload_path('media', pictures')
    """
    parts = ['upload']
    parts.extend(base_path)

    def func(instance, filename):
        path, ext = os.path.splitext(filename)
        rand = hashlib.sha1(uuid.uuid4().bytes).hexdigest()
        name = '%s%s' % (rand, ext)
        return os.path.join(*(parts + [name]))
    return func


class ChoiceEnum(enum.Enum):

    @classmethod
    def choices(cls):
        members = inspect.getmembers(cls, lambda m: not inspect.isroutine(m))
        props = [m for m in members if not m[0].startswith('_')]
        return tuple((value.value, key) for key, value in props)
