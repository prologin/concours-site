from django.core.management.base import BaseCommand
from problems.models import  SubmissionCode
from problems.tasks import submit_problem_code


class Command(BaseCommand):

    help = "Find uncorrected submissions with a non-empty celery_task_id and schedule them"

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help="Do not ask for confirmation")

    def handle(self, *args, **options):
        submissions = SubmissionCode.objects.filter(score__isnull=True).exclude(celery_task_id='')

        if not submissions:
            self.stderr.write("No uncorrected submissions found.")
            return

        self.stdout.write("Found {} uncorrected submissions.".format(len(submissions)))
        if not (options['confirm'] or input("Do you want to schedule them? [y/n] ") == "y"):
            self.stderr.write("Operation aborted.")
            return

        for submission in submissions:
            submit_problem_code.apply_async(args=[submission.pk], task_id=submission.celery_task_id, throw=False)
