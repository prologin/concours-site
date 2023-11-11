import contextlib
import logging
import requests
import subprocess
import tempfile
from contextlib import ExitStack
from django.utils.encoding import force_text

from problems.models import SubmissionCode
from problems.models.problem import Problem, Test, TestType
from prologin.utils import msgpack_dumps, msgpack_loads

logger = logging.getLogger(__name__)



def is_custom_check_valid(test: Test, output, custom_check, **kwargs) -> bool:
    """
    Check if a given `test` passes against `output` using the custom
    checker.
    **kwargs are passed verbatim to subprocess.check_call().

    May raise FileNotFoundError if checker program is not available.
    May raise other I/O errors if checker program fails at runtime.
    """

    @contextlib.contextmanager
    def filename_for(data):
        # already a file-like object: return its name
        if hasattr(data, 'read') and hasattr(data, 'name'):
            data.seek(0)
            yield data.name
            return
        # source string: store it in a temporary file
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.write(data)
            f.flush()
            yield f.name

    with ExitStack() as stack:
        # the checker program needs file paths as inputs;
        # create them using temporary files
        their_out_f, our_in_f, our_out_f = (
            stack.enter_context(filename_for(data))
            for data in (output, test.stdin, test.stdout))
        cmd = [custom_check, their_out_f, our_in_f, our_out_f]
        try:
            subprocess.check_call(
                cmd, #stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                **kwargs)
            return True
        except subprocess.SubprocessError:
            return False

def test_passes(reference: Test, test: dict, custom_check = None):
    """
    Defines what is a successful test:

    - exit code shall be zero
    - meta.status shall be OK
    - stdout must be ref. stdout (except for leading and trailing whitespaces)
    """
    # assume UnicodeDecode errors as contestant's garbage output
    stdout = force_text(test['stdout'], strings_only=False, errors='replace').strip()

    if custom_check is not None:
        return (test['exitcode'] == 0 and
            test['meta']['status'] == 'OK' and
            is_custom_check_valid(reference, stdout, custom_check))
    return (test['exitcode'] == 0 and
            test['meta']['status'] == 'OK' and
            stdout == reference.stdout.strip())


def get_score(problem: Problem, result: dict):
    """
    Compute raw score from level difficulty and compilation/test results.

    :param problem: the problem to solve
    :param result: the submission result from camisole
    :return the computed score
    """
    difficulty = problem.difficulty
    validation_percent = problem.validation_percent
    legacy = validation_percent is None
    reference_tests = {ref.name: ref for ref in problem.tests}

    if 'compile' in result and result['compile']['exitcode'] != 0:
        # compilation failure
        return 0

    if result.get('tests') is None:
        # no tests
        return 0

    custom_check = problem.custom_check

    total_correction = total_performance = passed_correction = passed_performance = 0
    for test in result['tests']:
        if not test:
            continue
        ref = reference_tests[test['name']]
        if ref.type is TestType.performance:
            total_performance += 1
            if test_passes(ref, test, custom_check):
                passed_performance += 1
        elif ref.type is TestType.correction:
            total_correction += 1
            if test_passes(ref, test, custom_check):
                passed_correction += 1

    if not total_correction:
        logger.warning("There is no correction test for problem %s", problem)

    if passed_correction != total_correction:
        # correction failure
        return 0

    if legacy:
        # Old scoring scheme <= 2023
        score = 16 * (4 ** difficulty)
        if total_performance:
            score = (score // 2) * (1 + passed_performance / total_performance)
    else:
        alpha = 0.42 # Quadratic term
        completion_factor = 4
        if difficulty == 0:
            score = 42
        else:
            score = 1000 * int(difficulty * (1 + alpha * difficulty))
        if total_performance:
            if passed_performance != total_performance:
                score_validation = validation_percent * score // 100
                score_performance = score - score_validation
                if passed_performance == 0:
                    score_performance = 0
                else:
                    score_performance *= (passed_performance / (completion_factor * total_performance - 2))
                score = score_validation + score_performance
    return int(score)


def submit(uri: str, code: SubmissionCode) -> dict:
    """
    Submit a code and its tests to a camisole worker listening at ``uri``.

    :param uri: HTTP address of the camisole worker
    :param code: the SubmissionCode to test
    :return: JSON-decoded result from camisole
    """
    request = code.generate_request()
    logger.debug("sending to camisole: %r", request)
    result = requests.post(
        uri,
        data=msgpack_dumps(request),
        headers={'content-type': 'application/msgpack',
                 'accept': 'application/msgpack'})
    result.raise_for_status()
    return msgpack_loads(result.content)
