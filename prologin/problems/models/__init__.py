from .submission import Submission, SubmissionCode, ExplicitProblemUnlock
from .problem import Challenge, Problem
from collections import namedtuple
from django.utils.translation import ugettext_lazy as _

ProblemEventType = namedtuple('ProblemEventType', 'code category display_name')
QUALIFICATION_TUP = ProblemEventType('qualifications', 'QCMs', _("Qualifications"))
REGIONAL_TUP = ProblemEventType('regionals', 'Demi-finales', _("Regional events"))

__all__ = [
    'Submission',
    'SubmissionCode',
    'ExplicitProblemUnlock',
    'Challenge',
    'Problem',
    'QUALIFICATION_TUP',
    'REGIONAL_TUP'
]
