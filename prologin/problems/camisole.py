import logging
import requests

from problems.models import SubmissionCode
from problems.models.problem import Problem, Test, TestType

logger = logging.getLogger(__name__)


def test_passes(reference: Test, test: dict):
    """
    Defines what is a successful test:

    - exit code shall be zero
    - meta.status shall be OK
    - stdout must be ref. stdout (except for leading and trailing whitespaces)
    """
    return (test['exitcode'] == 0 and
            test['meta']['status'] == 'OK' and
            test['stdout'].strip() == reference.stdout.strip())


def get_score(problem: Problem, result: dict):
    """
    Compute raw score from level difficulty and compilation/test results.

    :param problem: the problem to solve
    :param result: the submission result from camisole
    :return the computed score
    """
    difficulty = problem.difficulty
    reference_tests = {ref.name: ref for ref in problem.tests}

    if 'compile' in result and result['compile']['exitcode'] != 0:
        # compilation failure
        return 0

    if result.get('tests') is None:
        # no tests
        return 0

    total_correction = total_performance = passed_correction = passed_performance = 0
    for test in result['tests']:
        if not test:
            continue
        ref = reference_tests[test['name']]
        if ref.type is TestType.performance:
            total_performance += 1
            if test_passes(ref, test):
                passed_performance += 1
        elif ref.type is TestType.correction:
            total_correction += 1
            if test_passes(ref, test):
                passed_correction += 1

    if not total_correction:
        logger.warning("There is no correction test for problem %s", problem)

    if passed_correction != total_correction:
        # correction failure
        return 0

    score = 16 * (4 ** difficulty)
    if total_performance:
        score = (score // 2) * (1 + passed_performance / total_performance)
    return int(score)


def submit(uri: str, code: SubmissionCode) -> dict:
    """
    Submit a code and its tests to a camisole worker listening at ``uri``.

    :param uri: HTTP address of the camisole worker
    :param code: the SubmissionCode to test
    :return: JSON-decoded result from camisole
    """
    problem = code.submission.problem_model()

    def build_tests():
        for ref in problem.tests:
            yield {'name': ref.name, 'stdin': ref.stdin}

    language = code.language_enum()
    input = {
        'lang': language.value.camisole_name,
        'source': code.code,
        'all_fatal': True,
        'execute': problem.execution_limits(language),
        # FIXME: this is arbitrary
        'compile': {'cg-mem': int(1e7), 'time': 20, 'wall-time': 60, 'fsize': 4000},
        'tests': list(build_tests()),
    }
    logger.debug("sending to camisole: %r", input)
    result = requests.post(uri, json=input).json()
    return result
