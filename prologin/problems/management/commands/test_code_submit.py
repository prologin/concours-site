# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import argparse
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from prologin.languages import Language
from problems.models import Submission, SubmissionCode
from problems.tasks import submit_problem_code
import pprint


class Command(BaseCommand):
    help = "Test Celery submit_problem_code() task"

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('username')
        parser.add_argument('challenge')
        parser.add_argument('problem')
        parser.add_argument('language', choices=[lang.name for lang in Language])
        parser.add_argument('code', type=argparse.FileType('rb'))

    def handle(self, *args, **options):
        user = get_user_model().objects.get(username=options['username'])
        submission, created = Submission.objects.get_or_create(user=user,
                                                               challenge=options['challenge'],
                                                               problem=options['problem'])
        if created:
            submission.save()
        submission_code = SubmissionCode(submission=submission,
                                         language=Language[options['language']].name,
                                         code=options['code'].read())
        submission_code.save()
        self.stdout.write("Running task (4 second timeout)")
        result = submit_problem_code.apply_async(args=[submission_code.pk.id], throw=True)
        self.stdout.write(str(result.get(timeout=4)))

        submission = submission._meta.model.objects.get(pk=submission.pk)  # refresh

        self.stdout.write("Submission:")
        self.stdout.write(pprint.pformat(submission.__dict__))
        self.stdout.write("Latest code submission:")
        self.stdout.write(pprint.pformat(submission.latest_submission().__dict__))
