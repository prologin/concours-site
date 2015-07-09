from collections import namedtuple
from prologin.languages import Language
import datetime
import functools
import pytz

DEFAULT_TIME_ZONE = pytz.timezone('Europe/Paris')


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
    nt = namedtuple('Row', cursor.column_names)
    for row in cursor:
        yield nt(*row)


def date_localize(dt, tz):
    if dt.tzinfo is not None and dt.tzinfo == pytz.UTC:
        # actually is naive, MySQL returns tz=UTF as fallback
        return dt.replace(tzinfo=tz)
    return tz.localize(dt, is_dst=False)


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
    for ext in lang.value.extensions:
        map_from_legacy_language.mapping[ext] = lang