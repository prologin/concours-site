from collections import namedtuple
from django.core.files.base import ContentFile
from django.utils import timezone
import subprocess
from prologin.languages import Language
import prologin.models
import requests
import datetime
import functools
import os
import pytz

DEFAULT_TIME_ZONE = pytz.timezone('Europe/Paris')
CURRENT_TIMEZONE = timezone.get_current_timezone()


@functools.lru_cache(64)
def guess_timezone(offset):
    try:
        offset = abs(int(offset))
    except TypeError:
        return DEFAULT_TIME_ZONE
    if offset in (3600, 3600 * 2):
        return DEFAULT_TIME_ZONE
    for tz in pytz.all_timezones_set:
        tz = pytz.timezone(tz)
        tzoffset = tz.utcoffset(datetime.datetime(2015, 1, 1)).seconds
        if offset == tzoffset:
            return tz
    # No clue, just fallback
    return DEFAULT_TIME_ZONE


def nstrip(data, max_length=None):
    if data is None:
        return ""
    data = data.strip()
    if max_length is not None:
        return data[:max_length]
    return data


def namedcolumns(cursor):
    nt = namedtuple('Row', ','.join(e[0] for e in cursor.description))
    for row in cursor:
        yield nt(*row)


def date_localize(dt, tz):
    if dt.tzinfo is not None and dt.tzinfo == pytz.UTC:
        # actually is naive, MySQL returns tz=UTF as fallback
        return dt.replace(tzinfo=tz)
    return tz.localize(dt, is_dst=False)


def localize(date_or_datetime):
    def _localize(d: datetime.datetime):
        # is_dst not available in Django 1.8 make_aware(). Fuck this.
        # return timezone.make_aware(d, CURRENT_TIMEZONE, is_dst=True)
        if timezone.is_aware(d):
            return d
        return CURRENT_TIMEZONE.localize(d, is_dst=True)

    if isinstance(date_or_datetime, datetime.datetime):
        return _localize(date_or_datetime)
    elif isinstance(date_or_datetime, datetime.date):
        return _localize(datetime.datetime.combine(date_or_datetime, datetime.time.min))
    raise TypeError("localize() argument 1 must be one of datetime.date, datetime.datetime")


def field_fetch_file(session, field, url):
    try:
        field.open()
        return None
    except ValueError:
        # Standard use case
        pass
    except FileNotFoundError:
        # DB contains an avatar path that is not backed on disk, so download again
        pass
    try:
        req = session.get(url)
        if not req.ok:
            raise requests.RequestException("Status is not 2xx")
        field.save(os.path.split(url)[1], ContentFile(req.content))
        return True
    except requests.RequestException:
        return False


def parse_gender(what):
    what = what.lower().strip()
    if what == 'monsieur':
        return prologin.models.Gender.male.value
    elif what in ('madame', 'mademoiselle'):
        return prologin.models.Gender.female.value
    return None


def parse_php_birthday(serialized):
    # Don't ask, don't tell
    # a:3:{s:3:"day";s:2:"14";s:5:"month";s:1:"6";s:4:"year";s:4:"1988";}
    parts = serialized.split('{')[1].split(';')[:-1]
    extract = lambda k: k.split(':')[-1].strip('"')
    parts = {extract(k): int(extract(v)) for k, v in zip(parts[::2], parts[1::2])}
    return datetime.date(**parts)


def map_from_legacy_language(language_num):
    # www/sites/all/modules/training/training.module @ _training_get_lang()
    legacy = {
        0: {'doc': 'c', 'ext': ['.c'], 'title': 'C'},
        1: {'doc': 'cpp', 'ext': ['.cc', '.c++', '.cpp'], 'title': 'C++'},
        2: {'doc': 'pascal', 'ext': ['.pas', '.pascal'], 'title': 'Pascal'},
        3: {'doc': 'ocaml', 'ext': ['.ml', '.ocaml'], 'title': 'OCaml'},
        4: {'doc': 'java', 'ext': ['.java'], 'title': 'Java'},
        6: {'ext': ['.cs'], 'title': 'C#'},
        9: {'doc': 'python', 'ext': ['.py', '.python'], 'title': 'Python 2'},
        10: {'doc': 'ada', 'ext': ['.adb'], 'title': 'Ada'},
        11: {'doc': 'php', 'ext': ['.php'], 'title': 'PHP'},
        12: {'ext': ['.fs'], 'title': 'F#'},
        13: {'doc': 'scheme', 'ext': ['.scm'], 'title': 'Scheme'},
        14: {'doc': 'haskell', 'ext': ['.hs'], 'title': 'Haskell'},
        15: {'ext': ['.vb'], 'title': 'VB'},
        16: {'ext': ['.bf'], 'title': 'Brainf*ck'},
        17: {'ext': ['.js'], 'title': 'Javascript'},
        18: {'ext': ['.pl'], 'title': 'Perl'},
        19: {'ext': ['.py3'], 'title': 'Python 3'},
        20: {'ext': ['.lua'], 'title': 'Lua'},
    }
    try:
        return map_from_legacy_language.mapping[legacy[language_num]['ext'][0]]
    except KeyError:
        return None

map_from_legacy_language.mapping = {}
for lang in Language:
    for ext in lang.extensions():
        map_from_legacy_language.mapping[ext] = lang


def html_to_markdown(html):
    with subprocess.Popen(['pandoc', '--from', 'html', '--to', 'markdown'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as pandoc:
        return pandoc.communicate(html.encode('utf-8'))[0].decode('utf-8')
