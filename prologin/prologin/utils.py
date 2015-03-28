from django.template import VariableDoesNotExist, Variable
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

import enum
import hashlib
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
    Typical usage:
        FileField(upload_to=upload_path('media', 'pictures'))
    :param base_path: path of the directory (relative to MEDIA_ROOT) where to store the uploads
    :rtype callable
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
    @staticmethod
    def tr(func):
        """
        Constructs a class that overloads label_for() to apply :param func on the label.
        Typical usage:
            class MyEnum(ChoiceEnum.tr(str.title), ChoiceEnum):
                foo = 0
                bar = 1
                # Labels will be Foo and Bar.

        :param func: the callable to apply on raw labels; the result will be passed to
                     ugettext_lazy()
        :rtype class
        """
        label_for = classmethod(lambda cls, member: _(func(member.name)))
        return type('ChoiceEnumTr', (), {'label_for': label_for})

    @classmethod
    def label_for(cls, member):
        """
        Return the label for a given enum :param member.
        :param member: one of the members of this enum
        :return: (translated) string
        """
        return _(member.name)

    @classmethod
    def choices(cls, empty_label=None):
        """
        Generate a tuple of pairs suitable for Django's `choices` model field kwarg.
        :param empty_label: if provided, use this label instead of the default `-----`
                            for the empty value
        :rtype tuple of (db value, user facing string) pairs
        """
        choices = tuple((m.value, cls.label_for(m)) for m in cls)
        if empty_label:
            choices = ((None, empty_label),) + choices
        return choices
