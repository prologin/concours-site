import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from contest.models import Event


def lazy_getattr(self, item):
    """
    __getattr__ = lazy_getattr

    def _get_some_lazy(self):
        return expensive()

    def whatever(self):
        return self._some_lazy
    """
    getter = '_get{}'.format(item)
    func = getattr(self, getter)
    setattr(self, item, func())
    return getattr(self, item)


def read_props(filename):
    def parse(value):
        value = value.strip()
        value_lower = value.lower()
        if value.isnumeric() or (value.startswith('-') and value[1:].isnumeric()):
            return int(value)
        if value_lower in ('true', 'false'):
            return value_lower == 'true'
        return value

    with open(filename) as f:
        return {k.strip(): parse(v)
                for line in f if line.strip()
                for k, v in [line.split(':', 1)]}


class Challenge:
    """
    A Challenge is a group of problems for a given year and event type.
    Supported event types are:
        >>> from contest.models import Event
        >>> Event.Type.qualification
        >>> Event.Type.semifinal

    - Retrieve the full challenge list with:
        Challenge.all()
    - Get a challenge problem with:
        challenge.problems[i]
      You can sort problems by difficulty:
        sorted(challenge.problems, key=lambda p: p.difficulty)
    - Raw properties:
        challenge.properties
    - challenge.year
    - challenge.event_type
    - challenge.title
    - challenge.displayable
    - challenge.type
    """
    _type_to_low_level = {
        Event.Type.qualification: 'qcm',
        Event.Type.semifinal: 'demi',
    }

    __getattr__ = lazy_getattr

    @classmethod
    def all(cls):
        """
        Retrieve all challenges.

        :return list of Challenge instances
        """
        for challenge_dir in os.listdir(settings.TRAINING_PROBLEM_REPOSITORY_PATH):
            if not challenge_dir.startswith('.') and any(challenge_dir.startswith(e) for e in cls._type_to_low_level.values()):
                try:
                    yield Challenge.by_low_level_name(challenge_dir)
                except ObjectDoesNotExist:
                    pass

    @classmethod
    def by_low_level_name(cls, name):
        """
        Retrieve a challenge by its low-level name, such as 'demi2015'.
        """
        for event_type, keyword in cls._type_to_low_level.items():
            if name.startswith(keyword):
                break
        else:
            raise ObjectDoesNotExist("Unknown Challenge low-level event type: {}".format(name))
        year = name[len(keyword):]
        try:
            year = int(year)
        except ValueError:
            raise ObjectDoesNotExist("Invalid Challenge year: {}".format(year))
        return cls(year, event_type)

    @classmethod
    def by_year_and_event_type(cls, year, event_type):
        """
        Retrieve a challenge by its year and event type (Event.Type).
        """
        return cls(year, event_type)

    def __init__(self, year, event_type):
        assert isinstance(year, int)
        assert isinstance(event_type, Event.Type)
        self._low_level_name = '{}{}'.format(Challenge._type_to_low_level[event_type], year)
        self._year = year
        self._event_type = event_type
        path = self.file_path('challenge.props')
        if not os.path.exists(path):
            raise ObjectDoesNotExist("No such Challenge: not such file: {}".format(path))

    def file_path(self, *tail):
        return os.path.abspath(os.path.join(settings.TRAINING_PROBLEM_REPOSITORY_PATH, self._low_level_name, *tail))

    def _get_props(self):
        return read_props(self.file_path('challenge.props'))

    def _get_subject(self):
        with open(self.file_path('challenge.txt')) as f:
            return f.read()

    def _get_problems(self):
        # Do NOT use a generator
        problems = []
        for problem_dir in os.listdir(self.file_path()):
            if os.path.isdir(self.file_path(problem_dir)):
                try:
                    problems.append(Problem(self, problem_dir))
                except ObjectDoesNotExist:
                    pass
        return problems

    @property
    def year(self):
        return self._year

    @property
    def event_type(self):
        return self._event_type

    @property
    def name(self):
        return self._low_level_name

    @property
    def title(self):
        # We could return the title from props, but we can compute it directly
        return '{} {}'.format(Event.Type.label_for(self._event_type), self._year)

    @property
    def subject(self):
        return self._subject

    @property
    def displayable(self):
        return self._props.get('display_website', True)

    @property
    def type(self):
        return self._props.get('type')

    @property
    def problems(self):
        return self._problems

    @property
    def properties(self):
        return self._props


class Problem:
    """
    A challenge problem.

    - problem.subject
        > ('some text', 'markdown')
        or
        > ('some html', 'html')
    - Raw properties:
        challenge.properties
    - problem.title
    - problem.difficulty
    - problem.tests
    """
    __getattr__ = lazy_getattr

    def __init__(self, challenge, name):
        assert isinstance(challenge, Challenge)
        props_path = challenge.file_path(name, 'problem.props')
        if not os.path.exists(props_path):
            raise ObjectDoesNotExist("No such Problem: no such file: {}".format(props_path))
        self._challenge = challenge
        self._name = name

    def file_path(self, *tail):
        return self._challenge.file_path(self._name, *tail)

    def _get_props(self):
        return read_props(self.file_path('problem.props'))

    def _get_subject(self):
        subject_path_md = self.file_path('subject.md')
        subject_path_txt = self.file_path('subject.txt')
        if os.path.exists(subject_path_md):
            with open(subject_path_md) as f:
                return f.read(), 'markdown'
        elif os.path.exists(subject_path_txt):
            with open(subject_path_txt) as f:
                return f.read(), 'html'

    def _get_tests(self):
        tests = {}
        for item in os.listdir(self.file_path()):
            full_path = self.file_path(item)
            if item.endswith('.in') or item.endswith('.out'):
                with open(full_path) as f:
                    tests[item] = f.read()
        return tests

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._props.get('title')

    @property
    def difficulty(self):
        return self._props.get('difficulty', 0)

    @property
    def subject(self):
        return self._subject

    @property
    def tests(self):
        return self._tests

    @property
    def properties(self):
        return self._props
