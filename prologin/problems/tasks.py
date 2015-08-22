import urllib.parse

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction

from problems.corrector import remote_check, parse_xml
from problems.models import SubmissionCode

logger = get_task_logger('prologin.problems')


@shared_task
def submit_problem_code(code_submission_id):
    """
    Submit the code to the correction system. Update the database accordingly (score, malus).

    :param code_submission_id: primary key of a prologin.problems.models.SubmissionCode instance
    :return parse_xml() output
    """
    code_submission = SubmissionCode.objects.select_related('submission', 'submission__user').get(pk=code_submission_id)
    submission = code_submission.submission

    def get_score(difficulty, result):
        """
        Compute raw score from level difficulty and compilation/test results.
        :param difficulty: the level difficulty
        :param result: the submission result, as computed by parse_xml()
        :return the computed score
        """
        (compilation_ok, compilation_debug), tests = result

        if not compilation_ok:
            # compilation failure
            return 0

        total_correction = total_performance = passed_correction = passed_performance = 0
        for test in tests:
            if test['performance']:
                total_performance += 1
                if test['passed']:
                    passed_performance += 1
            else:
                total_correction += 1
                if test['passed']:
                    passed_correction += 1

        if not total_correction:
            logger.warning("There is no correction test for problem %s", submission)

        if passed_correction != total_correction:
            # correction failure
            return 0

        score = 16 * (4 ** difficulty)
        if total_performance:
            score = (score // 2) * (1 + passed_performance / total_performance)
        return int(score)

    def update_submission(difficulty, this_score, result):
        """
        Update the Submission and CodeSubmission.
        :param difficulty: the level difficulty
        :param this_score: the score, as computed by get_score()
        :param result: the submission result, as computed by parse_xml()
        """
        max_malus = 4 ** (difficulty + 1)
        # update main submission with this score, if needed
        if submission.score_base < this_score:
            submission.score_base = this_score
        # failed submission, no successful submission yet, not yet at maximum malus
        # so we can increment malus
        elif this_score == 0 and submission.score_base == 0 and submission.malus < max_malus:
            incr = int(4 ** (difficulty - 1))
            submission.malus += incr
            logger.info("Increased malus by %d to %d", incr, submission.malus)

        code_submission.score = this_score
        logger.info("Score is %d", code_submission.score)
        # TODO: implement when data available in VM
        # code_submission.exec_time = get exec_time from `result`
        # code_submission.exec_memory = get exec_memory from `result`
        with transaction.atomic():
            code_submission.save()
            submission.save()

    def submit(corrector_uri):
        """
        Submit `code_submission` using the corrector at `corrector_uri`.
        :param corrector_uri: the corrector URI
        :return the submission result, as computed by parse_xml()
        """
        uri = urllib.parse.urlsplit(corrector_uri)
        if uri.scheme == 'local':
            # TODO: implement, and refactor with the http (remote) code below
            prefix = uri.path
            raise NotImplementedError("Local correction is not implemented yet")

        elif uri.scheme in ('http', 'https'):
            # TODO: don't use a filename, pass the language code to VM
            filename = 'submission' + code_submission.language_def().extensions[0]
            result = remote_check(uri.geturl(), submission.challenge, submission.problem, code_submission.code,
                                  filename)
            result = parse_xml(result)
            logger.info("Raw result: %r", result)
            problem = submission.problem_model()
            difficulty = problem.difficulty
            score = get_score(difficulty, result)
            update_submission(difficulty, score, result)
            return result

        else:
            raise ValueError("Corrector URI '{}' has an unknown scheme".format(corrector_uri))

    # Try all TRAINING_CORRECTORS, in the order defined in settings
    # Stop at first working
    for corrector_uri in settings.TRAINING_CORRECTORS:
        try:
            logger.info("[%s] correcting: %s…", corrector_uri, code_submission)
            result = submit(corrector_uri)
            logger.info("[%s] corrected successfully: %s", corrector_uri, code_submission)
            return result
        except Exception:  # noqa
            logger.exception("[%s] corrector failed", corrector_uri)

    logger.error("All correctors failed to correct %s", code_submission)
