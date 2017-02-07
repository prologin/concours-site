import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from prometheus_client import Counter, Histogram

from problems import camisole
from problems.models import SubmissionCode

logger = get_task_logger('prologin.problems')

correction_status = Counter(
    'prologin_correction_status',
    "Problem submission correction status", ['problem', 'status'])
correction_score = Histogram(
    'prologin_correction_score',
    "Problem submission score by problem", ['problem'])


@shared_task(autoretry_for=(requests.RequestException,),
             default_retry_delay=3,
             retry_kwargs={'max_retries': 5})
def submit_problem_code(code_submission_id):
    """
    Submit the code to a camisole backend.
    Update the database with the result (including score & malus).

    :param code_submission_id: primary key of a
           prologin.problems.models.SubmissionCode instance
    :return raw result from camisole backend
    """
    code_submission = (SubmissionCode.objects
                       .select_related('submission', 'submission__user')
                       .get(pk=code_submission_id))
    submission = code_submission.submission
    problem = submission.problem_model()
    difficulty = problem.difficulty

    prometheus_stat_key = '{}/{}'.format(submission.challenge, submission.problem)

    def update_submission(score, result):
        """
        Update the Submission and CodeSubmission.
        :param score: the score, as computed by get_score()
        :param result: the submission result, as computed by parse_xml()
        """
        max_malus = 4 ** (difficulty + 1)
        # update main submission with this score, if needed
        if submission.score_base < score:
            submission.score_base = score
        # failed submission, no successful submission yet, not yet at maximum malus
        # so we can increment malus
        elif score == 0 and submission.score_base == 0 and submission.malus < max_malus:
            incr = int(4 ** (difficulty - 1))
            submission.malus += incr
            logger.debug("increased malus by %d to %d", incr, submission.malus)

        code_submission.score = score
        code_submission.result = result
        code_submission.date_corrected = timezone.now()

        # stats
        correction_score.labels(prometheus_stat_key).observe(code_submission.score)
        with transaction.atomic():
            code_submission.save()
            submission.save()

    # Try all PROBLEMS_CORRECTORS, in the order defined in settings
    # Stop at first working
    last_exc = None
    for corrector_uri in settings.PROBLEMS_CORRECTORS:
        try:
            logger.info("[%s] correcting: %s…", corrector_uri, code_submission)

            result = camisole.submit(corrector_uri, code_submission)
            logger.debug("camisole result: %r", result)
            if not result['success']:
                raise RuntimeError("camisole interal error:\n{}".format(result['error']))
            score = camisole.get_score(problem, result)
            update_submission(score, result)

            logger.info("[%s] corrected successfully: %s", corrector_uri, code_submission)
            correction_status.labels(prometheus_stat_key, 'ok').inc()
            return result
        except Exception as exc:  # noqa
            last_exc = exc
            logger.exception("[%s] corrector failed", corrector_uri)
            correction_status.labels(prometheus_stat_key, 'error').inc()

    logger.error("all correctors failed to correct %s", code_submission)
    raise last_exc
