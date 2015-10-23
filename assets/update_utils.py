import os
import shutil


def strip_components(path, n):
    path = os.path.normpath(path)
    return os.sep.join(path.split(os.sep)[n:])


def get_members_strip_prefix(zipball):
    parts = []
    for name in zipball.namelist():
        if not name.endswith('/'):
            parts.append(name.split('/')[:-1])
    prefix = os.path.commonprefix(parts) or ''
    if prefix:
        prefix = '/'.join(prefix) + '/'
    offset = len(prefix)
    for zipinfo in zipball.infolist():
        name = zipinfo.filename
        if len(name) > offset:
            zipinfo.filename = name[offset:]
            yield zipinfo


def extract_from_zip(zipball, member, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipball.open(member) as source, open(path, 'wb') as target:
        shutil.copyfileobj(source, target)
