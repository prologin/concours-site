from contextlib import contextmanager
import enum
import hashlib
import os
import random
import re
import string
import unicodedata
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.files import File
from django.core.urlresolvers import reverse
from django.utils.html import conditional_escape
from django.utils.translation import ugettext_lazy as _


def absolute_site_url(request, absolute_path):
    return "{protocol}://{host}{path}".format(
        protocol="https" if request.is_secure() else "http",
        host=settings.SITE_HOST,
        path=absolute_path,
    )


def get_slug(name):
    name = unicodedata.normalize('NFKD', name.lower())
    name = ''.join(x for x in name if x in string.ascii_letters + string.digits + ' _-')
    name = re.sub(r'[^a-z0-9\-]', '_', name)
    return name


def sizeof_fmt(num: int, suffix='B'):
    for unit in ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'):
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def upload_path(*base_path, using=None):
    """
    Generate upload path for a FileInput.
    Typical usage:

        class Whatever:
            def upload_to_pictures(self, *args, **kwargs):
                return upload_path('media', 'pictures')(self, *args, **kwargs)

            image = FileField(upload_to=upload_to_pictures)

    :param base_path: path components to the directory (relative to MEDIA_ROOT)
    where to store the uploads
    :param using: None to use a random file name
                  or callable(instance) that returns bytes to generate a
                  predictable filename
    :rtype callable
    """
    parts = ['upload']
    parts.extend(base_path)

    def func(instance, filename):
        if using is None:
            data = uuid.uuid4().bytes
        else:
            data = using(instance)
        data = b''.join((settings.SECRET_KEY.encode(), data))
        name = hashlib.sha1(data).hexdigest()
        path, ext = os.path.splitext(filename)
        name += ext
        return os.path.join(*(parts + [name]))

    return func


class LoginRequiredMixin:
    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(view)


class ChoiceEnum(enum.Enum):
    @staticmethod
    def labels(func):
        """
        Constructs a class that overloads label_for() to apply :param func on the label.
        LT stands for Label Transform.
        Typical usage:
            @ChoiceEnum.with_labels(str.title)
            class MyEnum(ChoiceEnum):
                foo = 0
                bar = 1
                # Labels will be Foo and Bar.

        :param func: the callable to apply on raw labels; the result will be passed to
                     ugettext_lazy()
        :rtype class
        """
        assert callable(func)

        def classbuilder(klass):
            klass.label_for = classmethod(lambda cls, member: _(func(member.name)))
            return klass

        return classbuilder

    @staticmethod
    def sort(key=None, reverse=False):
        """
        Constructs a class that overloads _get_choices() to sort the choices using :param key
        and :param reverse.
        :param key: callable to use for sorting; if None, sorts by label (case insensitive)
        :param reverse: reverse the sort order
        :rtype: class
        """
        if key is None:
            key = lambda pair: pair[1].lower()
        else:
            assert callable(key)

        def classbuilder(klass):
            orig_get_choices = klass._get_choices
            klass._get_choices = classmethod(lambda cls: sorted(orig_get_choices(), key=key, reverse=reverse))
            return klass

        return classbuilder

    @classmethod
    def label_for(cls, member):
        """
        Return the label for a given enum :param member.
        :param member: one of the members of this enum
        :return: (translated) string
        """
        return _(member.name)

    @classmethod
    def _get_choices(cls):
        """
        Override this method in your ChoiceEnum subclass if you need to implement custom
        behavior, eg. if your members are not of the form "name = db_value".
        :return tuple of (db value, user facing string) pairs
        """
        return tuple((m.value, cls.label_for(m)) for m in cls)

    @classmethod
    def choices(cls, empty_label=None):
        """
        Generate a tuple of pairs suitable for Django's `choices` model field kwarg.
        :param empty_label: if provided, use this label instead of the default `-----`
                            for the empty value
        :rtype tuple of (db value, user facing string) pairs
        """
        choices = cls._get_choices()
        if empty_label:
            choices = ((None, empty_label),) + choices
        return choices


def cached(func, cache_setting_name, **kwargs):
    assert callable(func)
    cache_setting = settings.PROLOGIN_CACHES[cache_setting_name]
    key = cache_setting.key
    if kwargs:
        key = key.format(**kwargs)
    value = cache.get(key)
    if value is None:
        value = func()
        cache.set(key, value, cache_setting.duration)
    return value


def admin_url_for(model_admin, obj, method='change', label=lambda e: str(e)):
    if obj is None:
        return model_admin.get_empty_value_display()
    return '<a href="{}">{}</a>'.format(reverse('admin:{}_{}_{}'.format(obj._meta.app_label, obj._meta.model_name, method),
                                                args=[obj.pk]), conditional_escape(label(obj)))


ENCODINGS = ('utf-8-sig', 'utf-8', 'latin1')


def read_try_hard(fileobj: File, *args, encodings=ENCODINGS):
    data = fileobj.read(*args)
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ValueError("Could not find proper encoding (tried {}) for file: {}"
                     .format(', '.join(ENCODINGS), fileobj))


def open_try_hard(callback, filename, *args, encodings=ENCODINGS, **kwargs):
    """
    Small wrapper around open() that tries to apply `callback` on all
    encodings from `encodings` (in order) instead of failing directly on
    UnicodeDecodeError.
    """
    for encoding in encodings:
        try:
            kwargs['encoding'] = encoding
            with open(filename, *args, **kwargs) as f:
                return callback(f)
        except UnicodeDecodeError:
            pass
    else:
        raise ValueError("Could not find proper encoding (tried {}) for file: {}"
                         .format(', '.join(ENCODINGS), filename))


def lazy_attr(prop_name, getter):
    def wrapped(self, *args, **kwargs):
        try:
            return getattr(self, prop_name)
        except AttributeError:
            data = getter(self, *args, **kwargs)
            setattr(self, prop_name, data)
            return data
    return property(wrapped)


def read_props(filename):
    def parse(value):
        value = value.strip()
        value_lower = value.lower()
        if value.isnumeric() or (value.startswith('-') and value[1:].isnumeric()):
            return int(value)
        if value_lower in ('true', 'false'):
            return value_lower == 'true'
        return value

    def props(f):
        return {k.strip(): parse(v)
                for line in f if line.strip()
                for k, v in [line.split(':', 1)]}
    return open_try_hard(props, filename)


def translate_format(format_str):
    rep = {"%Y": _("year")[0] * 4,
           "%m": _("month")[0] * 2,
           "%d": _("day")[0] * 2}
    # single-pass replacement
    rep = {re.escape(k): v for k, v in rep.items()}
    return re.sub("|".join(rep.keys()), lambda m: rep[re.escape(m.group(0))], format_str)


@contextmanager
def save_random_state(seed=None):
    state = random.getstate()
    if seed is not None:
        random.seed(seed)
    yield
    random.setstate(state)


class SubprocessFailedException(Exception):
    def __init__(self, message, returncode, stdout, stderr):
        self.message = message
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
