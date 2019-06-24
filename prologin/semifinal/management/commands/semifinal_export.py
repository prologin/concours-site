# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import argparse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.management import BaseCommand, CommandError

import contest.models
import problems.models

User = get_user_model()


class Command(BaseCommand):
    help = "Export semifinal result data for upload in production website."

    def add_arguments(self, parser):
        parser.add_argument('export_file', type=argparse.FileType('w'))

    def abort(self, msg=None):
        raise CommandError(msg)

    def handle(self, *args, **options):
        if not settings.PROLOGIN_SEMIFINAL_MODE:
            self.abort("Your are not in semifinal mode.")

        event = contest.models.Event.objects.select_related('edition').get()

        users = User.objects.filter(is_active=True, is_staff=False, is_superuser=False)
        contestants = contest.models.Contestant.objects.filter(edition=event.edition, user__in=users)

        if len(users) != len(contestants):
            self.abort("Number of users and contestants do not match.")

        challenge = problems.models.Challenge.by_year_and_event_type(event.edition.year, contest.models.Event.Type.semifinal)
        submissions = problems.models.Submission.objects.filter(user__in=users, challenge=challenge.name)
        codes = problems.models.SubmissionCode.objects.filter(submission__in=submissions)
        unlocks = problems.models.ExplicitProblemUnlock.objects.filter(challenge=challenge.name, user__in=users)

        serializer = serializers.get_serializer('json')()

        stream = options['export_file']

        serializer.serialize([event.edition], stream=stream)
        stream.write("\n")
        serializer.serialize([event.center], stream=stream)
        stream.write("\n")
        serializer.serialize([event], stream=stream)
        stream.write("\n")
        serializer.serialize(users, fields=('pk',), stream=stream)
        stream.write("\n")
        serializer.serialize(contestants,
                             fields=('edition', 'user', 'score_semifinal_written', 'score_semifinal_interview',
                                     'score_semifinal_machine', 'score_semifinal_bonus'),
                             stream=stream)
        stream.write("\n")
        serializer.serialize(submissions, stream=stream)
        stream.write("\n")
        serializer.serialize(codes,
                             fields=('submission', 'language', 'code',
                                     'summary', 'score', 'date_submitted',
                                     'date_corrected'),
                             stream=stream)
        stream.write("\n")
        serializer.serialize(unlocks, stream=stream)
        stream.close()

        self.stdout.write("Exported")
        self.stdout.write("  {:>4} users".format(len(users)))
        self.stdout.write("  {:>4} contestants".format(len(contestants)))
        self.stdout.write("  {:>4} submissions".format(len(submissions)))
        self.stdout.write("  {:>4} codes".format(len(codes)))
        self.stdout.write("  {:>4} explicit unlocks".format(len(unlocks)))
