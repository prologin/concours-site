from collections import namedtuple
from django import db
from django.conf import settings
from django.core.management.base import BaseCommand
from prologin.languages import Language
import datetime
import functools
import os
import pytz

import users.models
import prologin.utils

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


# www/sites/all/modules/training/training.module @ _training_get_lang()
@functools.lru_cache(32)
def map_from_legacy_language(language_num):
    mapping = {}
    for lang in Language:
        for ext in lang.value.exts:
            mapping[ext] = lang.name
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
        return mapping[legacy[language_num]['ext'][0]]
    except KeyError:
        return ""


USER_QUERY = """
SELECT
  u.uid,
  status,
  name,
  mail,
  signature,
  timezone,
  picture,
  training_language,
  u.birthday                                    AS u_birthday,
  IF(created > 0, FROM_UNIXTIME(created), NULL) AS created,
  IF(access > 0, FROM_UNIXTIME(access), NULL)   AS access,
  IF(login > 0, FROM_UNIXTIME(login), NULL)     AS login,
  NOT(ISNULL(urc.uid))                          AS is_staff,
  NOT(ISNULL(ura.uid))                          AS is_superuser,
  pvg.value                                     AS gender,
  pvln.value                                    AS ln,
  pvfn.value                                    AS fn,
  pvbd.value                                    AS p_birthday,
  pvp.value                                     AS country,
  pvl.value                                     AS grade,
  pvaa.value                                    AS a_addr,
  pvap.value                                    AS a_code,
  pvac.value                                    AS a_city,
  NOT (pvnm.value)                              AS mailing,
  pvph.value                                    AS phone
FROM users u
  LEFT JOIN users_roles urc ON urc.uid = u.uid AND urc.rid = 6
  LEFT JOIN users_roles ura ON ura.uid = u.uid AND ura.rid = 7
  LEFT JOIN profile_values pvg ON pvg.uid = u.uid AND pvg.fid = 1
  LEFT JOIN profile_values pvln ON pvln.uid = u.uid AND pvln.fid = 2
  LEFT JOIN profile_values pvfn ON pvfn.uid = u.uid AND pvfn.fid = 3
  LEFT JOIN profile_values pvbd ON pvbd.uid = u.uid AND pvbd.fid = 5
  LEFT JOIN profile_values pvp ON pvp.uid = u.uid AND pvp.fid = 6
  LEFT JOIN profile_values pvl ON pvl.uid = u.uid AND pvl.fid = 7
  LEFT JOIN profile_values pvaa ON pvaa.uid = u.uid AND pvaa.fid = 8
  LEFT JOIN profile_values pvap ON pvap.uid = u.uid AND pvap.fid = 9
  LEFT JOIN profile_values pvac ON pvac.uid = u.uid AND pvac.fid = 10
  LEFT JOIN profile_values pvnm ON pvnm.uid = u.uid AND pvnm.fid = 11
  LEFT JOIN profile_values pvph ON pvph.uid = u.uid AND pvph.fid = 12
WHERE u.name IS NOT NULL AND u.name != '' AND u.mail != ''
GROUP BY u.uid
ORDER BY u.uid ASC
"""


class Command(BaseCommand):
    help = "Move data from old, shitty MySQL database to the shinny new Postgres one."

    def migrate_users(self, mysql):
        print("Migrating users")
        new_users = []
        with mysql.cursor() as c:
            c.execute(USER_QUERY)
            for row in namedcolumns(c):
                avatar = None
                if row.picture:
                    avatar = prologin.utils.upload_path('avatar')(None, os.path.split(row.picture)[1])
                p_birthday = None
                birthday = None
                if row.p_birthday:
                    p_birthday = parse_php_birthday(row.p_birthday)
                if row.u_birthday and p_birthday and row.u_birthday != p_birthday:
                    print("Different u/p birthday:", row.u_birthday, p_birthday)
                    birthday = p_birthday
                elif row.u_birthday and not p_birthday:
                    birthday = row.u_birthday
                elif p_birthday and not row.u_birthday:
                    birthday = p_birthday
                gender = None
                if row.gender is not None:
                    gender = users.models.ProloginUser.Gender.m.name if row.gender == 'Monsieur' \
                        else users.models.ProloginUser.Gender.f.name
                user_timezone = guess_timezone(row.timezone)
                date_joined = min(date for date in (row.created, row.access, row.login) if date)
                last_login = max(date for date in (row.created, row.access, row.login) if date)
                if len(row.name) > 30:
                    print("Ignoring too long:", row.uid, row.name)
                    continue
                user = users.models.ProloginUser(
                    pk=row.uid, username=row.name, email=row.mail, first_name=nstrip(row.fn, 30), last_name=nstrip(row.ln, 30),
                    phone=nstrip(row.phone, 16), address=nstrip(row.a_addr), postal_code=nstrip(row.a_code, 32),
                    city=nstrip(row.a_city, 64), country=nstrip(row.country, 64), birthday=birthday,
                    school_stage=row.grade, signature=row.signature, avatar=avatar, gender=gender,
                    timezone=user_timezone, allow_mailing=bool(row.mailing),
                    preferred_language=map_from_legacy_language(row.training_language),
                    date_joined=date_localize(date_joined, user_timezone),
                    last_login=date_localize(last_login, user_timezone), is_active=bool(row.status),
                    is_superuser=bool(row.is_superuser), is_staff=bool(row.is_superuser) or bool(row.is_staff),
                )
                new_users.append(user)
        print("Now adding users to new DBs")
        with db.transaction.atomic():
            users.models.ProloginUser.objects.bulk_create(new_users)

    def handle(self, *args, **options):
        # check if we can access the legacy db
        # mc is MySQL cursor
        mysql = db.connections['mysql_legacy']
        with mysql.cursor() as c:
            c.execute('SHOW TABLES')
            tables = c.fetchall()
        print("Found {} tables".format(len(tables)))

        self.migrate_users(mysql)
        # TODO: the rest
