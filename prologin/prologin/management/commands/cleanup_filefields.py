# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import os
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db.models import FileField
from django.conf import settings


def listdir(prefix, path):
    for root, dirs, files in os.walk(path):
        for file in files:
            yield os.path.relpath(os.path.join(root, file), prefix)


class Command(BaseCommand):
    help = "Delete obsolete files from FileFields"

    def handle(self, *args, **options):
        db_files = {}

        for model in apps.get_models():
            if model._meta.proxy or model._meta.abstract:
                continue

            for field in model._meta.get_fields():
                if not issubclass(field.__class__, FileField):
                    continue

                fname = field.get_attname()
                objects = (model._base_manager
                           .exclude(**{'%s__isnull' % fname: True})
                           .exclude(**{fname: ''})
                           .distinct())

                db_files.update({getattr(o, fname): o for o in objects})

        disk_files = set(listdir(settings.MEDIA_ROOT, settings.MEDIA_ROOT))

        self.stdout.write("Files in DB not in disk:")
        diff = db_files.keys() - disk_files
        if diff:
            self.stdout.write("{}".format(len(diff)))
            self.stdout.write("{}".format([db_files[k] for k in db_files.keys() - disk_files]))
        else:
            self.stdout.write("None!")

        self.stdout.write("")
        self.stdout.write("Files in disk not in DB:")
        diff = disk_files - db_files.keys()
        if diff:
            self.stdout.write("{}".format(len(diff)))
            for file in diff:
                path = os.path.join(settings.MEDIA_ROOT, file)
                self.stdout.write("rm {}".format(path))
                os.remove(path)
        else:
            self.stdout.write("None!")
        self.stdout.write("")
