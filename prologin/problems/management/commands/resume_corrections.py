# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.core.management.base import BaseCommand
from django.db import transaction
import celery

from problems.models import SubmissionCode
from problems.tasks import submit_problem_code


class Command(BaseCommand):

    help = "Find uncorrected submissions with a non-empty celery_task_id and schedule them"

    def add_arguments(self, parser):
        parser.add_argument('--renew', action='store_true', help="Renew the task ID")
        parser.add_argument('--yes', action='store_true', help="Do not ask for confirmation")

    def get_submissions(self):
        return SubmissionCode.objects.filter(score__isnull=True).exclude(celery_task_id='')

    def handle(self, *args, **options):
        submissions = self.get_submissions()

        if not submissions:
            self.stderr.write("No uncorrected submissions found.")
            return

        self.stdout.write("Found {} uncorrected submissions.".format(len(submissions)))
        if not (options['yes'] or input("Do you want to schedule them? [y/n] ") == "y"):
            self.stderr.write("Operation aborted.")
            return

        if options['renew']:
            with transaction.atomic():
                for submission in submissions:
                    submission.celery_task_id = celery.uuid()
                    submission.save()

        for submission in self.get_submissions():
            self.stdout.write('{}: {}'.format(submission.pk, submission.celery_task_id))
            submit_problem_code.apply_async(args=[submission.pk], task_id=submission.celery_task_id)
