import argparse
import gzip
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.management import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

import contest.models

User = get_user_model()


class Command(BaseCommand):
    help = "Export semifinal data for bootstraping."

    def add_arguments(self, parser):
        parser.add_argument('-y', '--year', type=int, help="Year", default=settings.PROLOGIN_EDITION)
        parser.add_argument('export_file', type=argparse.FileType('wb'))

    def abort(self, msg=None):
        raise CommandError(msg)

    def handle(self, *args, **options):
        transaction.set_autocommit(False)

        year = options['year']
        events = list(contest.models.Event.semifinals_for_edition(year).order_by('date_begin'))

        self.stdout.write("{} events:".format(year))
        len_event = len(events)

        for i, event in enumerate(events, 1):
            self.stdout.write("{:>2d}. {}: {}".format(i, event.date_begin.strftime("%Y-%m-%d"), event.center.name))

        while True:
            try:
                self.stdout.write("\nEvent number to bootstrap: ", ending="")
                event_id = int(input())
                if not 1 <= event_id <= len_event:
                    raise ValueError
                break
            except ValueError:
                pass
            except (EOFError, KeyboardInterrupt):
                return self.abort("Interrupted")

        event = events[event_id - 1]

        self.stdout.write("\nExporting {}: {}".format(event.date_begin.strftime("%Y-%m-%d"), event.center.name))

        contestants = (event.assigned_contestants
                       .select_related('user')
                       .filter(user__is_active=True, user__is_staff=False, user__is_superuser=False)
                       .all())

        serializer = serializers.get_serializer('json')()

        def iter_users():
            for contestant in contestants:
                user = contestant.user
                user.set_password(user.plaintext_password)
                user.username = user.normalized_username
                self.stdout.write("        {}".format(user.username))
                yield user

        def iter_contestants():
            for contestant in contestants:
                self.stdout.write("        {}".format(contestant.user.username))
                yield contestant

        with gzip.open(options['export_file'], mode='wt') as file:
            self.stdout.write("    Edition")
            serializer.serialize([event.edition], stream=file)
            file.write("\n")
            self.stdout.write("    Center")
            serializer.serialize([event.center], stream=file)
            file.write("\n")
            self.stdout.write("    Event")
            serializer.serialize([event], stream=file)
            file.write("\n")
            self.stdout.write("    Users")
            serializer.serialize(iter_users(),
                                 fields=('username', 'email', 'password', 'first_name', 'last_name', 'phone',
                                         'preferred_locale'),
                                 stream=file)
            file.write("\n")
            self.stdout.write("    Contestants")
            serializer.serialize(iter_contestants(),
                                 fields=('edition', 'user', 'preferred_language', 'score_qualif_qcm', 'score_qualif_algo',
                                         'score_qualif_bonus'),
                                 stream=file)
