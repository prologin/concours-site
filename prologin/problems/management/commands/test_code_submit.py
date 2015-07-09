from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from prologin.languages import Language
from problems.models import Submission, SubmissionCode
from problems.tasks import submit_problem_code
import pprint


class Command(BaseCommand):

    args = "username challenge problem language code"
    help = "Test Celery submit_problem_code() task"

    def handle(self, *args, **options):
        user, challenge, problem, lang, code = args

        user = get_user_model().objects.get(username=user)
        submission, created = Submission.objects.get_or_create(user=user, challenge=challenge, problem=problem)
        if created:
            submission.save()
        submission_code = SubmissionCode(submission=submission, language=Language[lang].name, code=code)
        submission_code.save()
        print("Running task (4 second timeout)")
        result = submit_problem_code.apply_async(args=[submission_code.pk], throw=True)
        print(result.get(timeout=4))

        submission = submission._meta.model.objects.get(pk=submission.pk)  # refresh

        print()
        print("Submission:")
        pprint.pprint(submission.__dict__)
        print()
        print("Latest code submission:")
        pprint.pprint(submission.latest_submission().__dict__)