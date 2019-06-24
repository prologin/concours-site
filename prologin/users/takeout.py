# Copyright (C) <2018> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

"""Contains the utilities used to bundle all the personal data of a given user
into a tarball and export it.
"""

import datetime
import io
import yaml
import os
import pathlib
import tarfile
import tempfile

from contest.models import ShirtSize
from prologin.languages import Language
from prologin.models import Gender
from users.models import EducationStage


def dump(data):
    return yaml.dump(data, default_flow_style=False, allow_unicode=True)


def tar(path, arcname, compression='gz'):
    obj = io.BytesIO()
    with tarfile.open(fileobj=obj, mode='w:' + compression) as tar:
        tar.add(path, arcname=arcname)
    return obj.getvalue()


def takeout(user):
    with tempfile.TemporaryDirectory(prefix='prologin-takeout-') as td:
        takeout_dir = pathlib.Path(td)
        export_user_fields(user, takeout_dir)
        export_avatar(user, takeout_dir)
        export_all_contestants(user, takeout_dir)
        export_all_codes(user, takeout_dir / 'codes')
        export_all_forum_posts(user, takeout_dir / 'forum')
        arcname = '{}-{}'.format(user.username, datetime.date.today())
        return tar(td, arcname), arcname


def export_user_fields(user, path):
    # Gender
    try:
        gender = Gender(user.gender).name
    except ValueError:
        gender = None

    # School Stage
    school_stage = [str(e.value[1]) for e in EducationStage
                    if e.value[0] == user.school_stage]
    if school_stage:
        school_stage = school_stage[0]
    else:
        school_stage = None

    data = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'gender': gender,
        'phone': user.phone,
        'school_stage': school_stage,
        'birthday': str(user.birthday),

        'address': user.address,
        'postal_code': user.postal_code,
        'city': user.city,
        'country': user.country,

        'last_login': str(user.last_login),
        'date_joined': str(user.date_joined),
        'preferred_language': user.preferred_language,
        'timezone': str(user.timezone),
        'preferred_locale': str(user.preferred_locale),

    }
    serialized_data = dump(data)
    (path / 'user.yml').write_text(serialized_data)


def export_avatar(user, path):
    if not user.avatar:
        return
    try:
        with user.avatar.open() as avatar_f:
            avatar = avatar_f.read()
    except FileNotFoundError:
        return
    _, ext = os.path.splitext(user.avatar.name)
    (path / ('avatar' + ext)).write_bytes(avatar)


def export_all_forum_posts(user, forum_dir):
    forum_dir.mkdir()
    for post in user.forum_posts.all():
        thread_dir_name = '{}-{}'.format(post.thread.id, post.thread.slug)
        thread_dir = forum_dir / thread_dir_name
        thread_dir.mkdir(exist_ok=True)
        post_file = thread_dir / ('{}.md'.format(post.id))
        post_file.write_text(post.content)


def export_all_contestants(user, path):
    data = {}
    for contestant in user.contestants.all():
        # School
        if contestant.school:
            school_name = contestant.school.name
        else:
            school_name = None

        # Preferred language
        try:
            pref_lang = Language[contestant.preferred_language].name_display()
        except KeyError:
            pref_lang = contestant.preferred_language

        # Shirt size
        try:
            shirt_size = ShirtSize(contestant.shirt_size).name.upper()
        except ValueError:
            shirt_size = None

        data[str(contestant.edition.year)] = {
            'school': school_name,
            'shirt_size': shirt_size,
            'preferred_language': pref_lang,
        }
    if data:
        serialized_data = dump(data)
        serialized_path = path / 'participations.yml'
        serialized_path.write_text(serialized_data)


def export_all_codes(user, code_dir):
    code_dir.mkdir()
    for submission in user.training_submissions.all():
        codes = submission.codes.all()
        if not codes:
            continue
        problem_dir = code_dir / submission.challenge / submission.problem
        problem_dir.mkdir(parents=True)
        for code in codes:
            ts = str(int(code.date_submitted.timestamp()))
            try:
                ext = Language[code.language].extensions()[0]
            except KeyError:  # deleted languages
                ext = '.' + code.language
            code_file = problem_dir / (ts + ext)
            code_file.write_text(code.code)
