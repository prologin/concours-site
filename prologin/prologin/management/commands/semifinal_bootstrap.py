import argparse

import getpass
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.management import BaseCommand, CommandError
from django.db import transaction

from contest.models import Edition, Center, Event, Contestant

User = get_user_model()


class Command(BaseCommand):
    help = "Bootstrap a semifinal website."
    args = "<import-file>"

    def add_arguments(self, parser):
        parser.add_argument('import_file', type=argparse.FileType('r'))

    def abort(self, msg=None):
        raise CommandError(msg)

    def _write(self, file, fmt, *args, **kwargs):
        if isinstance(fmt, str):
            fmt = fmt.format(*args, **kwargs)
        else:
            if args or kwargs:
                raise TypeError()
            fmt = str(fmt)
        return file.write(fmt)

    def print(self, format="", *args, **kwargs):
        self._write(self.stdout, format, *args, **kwargs)

    def error(self, format="", *args, **kwargs):
        self._write(self.stderr, format, *args, **kwargs)

    def db_not_empty(self, type):
        self.abort("Database is not empty: it contains {} objects. Please clear the database to a post-migrate state "
                   "before bootstrapping a semifinal.".format(type))

    def handle(self, *args, **options):
        # Safety checks
        if 'semifinal' not in settings.INSTALLED_APPS:
            self.abort("Module 'semifinal' is not in INSTALLED_APPS. Please ensure you are using semifinal settings.")

        for model in (Edition, Event, Center, Contestant, User):
            if model.objects.exists():
                return self.db_not_empty(model.__class__.__name__)

        deserializer = serializers.get_deserializer('json')

        file = options['import_file']
        with transaction.atomic():
            edition = next(deserializer(file.readline()))
            self.print("    Edition    {}", edition.object)
            edition.save()
            center = next(deserializer(file.readline()))
            self.print("    Center     {}", center.object)
            center.save()
            event = next(deserializer(file.readline()))
            self.print("    Event      {}", event.object)
            event.save()
            for user in deserializer(file.readline()):
                self.print("    User       {}", user.object.username)
                user.save()
            for contestant in deserializer(file.readline()):
                self.print("    Contestant {}", contestant.object.user.username)
                contestant.save()

            # Admin user
            self.print("\nCreating admin user 'admin'.")
            while True:
                self.print("Provide a password for user 'admin': ")
                password = getpass.getpass("")
                if password:
                    break
            admin = User(username='admin', email='admin@prologin.org',
                         is_active=True, is_superuser=True, is_staff=True)
            admin.set_password(password)
            admin.save()

            self.print("Bootstrapping completed.")
