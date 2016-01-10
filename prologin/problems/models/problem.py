import enum
import os
from collections import namedtuple
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from contest.models import Event
from prologin.languages import Language
from prologin.utils import open_try_hard, lazy_attr, read_props


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

    class Type(enum.Enum):
        standard = 'all-available'
        all_per_level = 'all-by-level'
        one_per_level = 'one-by-level'
        one_per_level_delayed = 'one-by-level-with-delay'

    @classmethod
    def all(cls):
        """
        Retrieve all challenges.

        :return list of Challenge instances
        """
        for challenge_dir in os.listdir(settings.PROBLEMS_REPOSITORY_PATH):
            if not challenge_dir.startswith('.') and any(challenge_dir.startswith(e)
                                                         for e in cls._type_to_low_level.values()):
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
    def by_year_and_event_type(cls, year: int, event_type: Event.Type):
        """
        Retrieve a challenge by its year and event type (Event.Type).
        """
        return cls(year, event_type)

    def __init__(self, year, event_type):
        assert isinstance(year, int)
        assert isinstance(event_type, Event.Type)
        try:
            self._low_level_name = '{}{}'.format(
                    Challenge._type_to_low_level[event_type], year)
        except KeyError:
            raise ObjectDoesNotExist("No Challenge for event type: {}".format(
                event_type))
        self._year = year
        self._event_type = event_type
        path = self.file_path('challenge.props')
        if not os.path.exists(path):
            raise ObjectDoesNotExist("No such Challenge: no such file: {}".format(path))

    def __hash__(self):
        return hash(self._low_level_name)

    def __eq__(self, other):
        return other._low_level_name == self._low_level_name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Challenge: {} {}>'.format(self.event_type.name, self.year)

    def file_path(self, *tail):
        return os.path.abspath(os.path.join(settings.PROBLEMS_REPOSITORY_PATH, self._low_level_name, *tail))

    def _get_properties(self):
        return read_props(self.file_path('challenge.props'))
    properties = lazy_attr('_properties_', _get_properties)

    def _get_subject(self):
        return open_try_hard(lambda f: f.read(), self.file_path('challenge.txt'))
    subject = lazy_attr('_subject_', _get_subject)

    def _get_problems(self):
        # Do NOT use a generator
        problems = []
        for problem_dir in os.listdir(self.file_path()):
            if os.path.isdir(self.file_path(problem_dir)):
                try:
                    problems.append(Problem(self, problem_dir))
                except ObjectDoesNotExist:
                    pass
        return sorted(problems)
    problems = lazy_attr('_problems_', _get_problems)

    def problems_of_difficulty(self, difficulty):
        return sorted(problem for problem in self.problems if problem.difficulty == difficulty)

    @property
    def year(self) -> int:
        return self._year

    @property
    def event_type(self) -> Event.Type:
        return self._event_type

    @property
    def name(self) -> str:
        return self._low_level_name

    @property
    def title(self) -> str:
        # We could return the title from props, but we can compute it directly
        return '{} {}'.format(Event.Type.label_for(self._event_type), self._year)

    @property
    def displayable(self):
        return self.properties.get('display_website', False)

    @property
    def type(self) -> Type:
        return Challenge.Type(self.properties.get('type'))

    @property
    def auto_unlock_delay(self) -> int:
        """
        The amount of seconds to wait before auto-unlocking new problem(s).
        """
        return self.properties.get('unlock_delay', settings.PROLOGIN_PROBLEM_DEFAULT_AUTO_UNLOCK_DELAY)

    @property
    def problem_difficulty_list(self) -> [int]:
        return sorted(set(problem.difficulty for problem in self.problems))


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

    Sample = namedtuple('Sample', 'input output comment')

    def __init__(self, challenge, name):
        assert isinstance(challenge, Challenge)
        props_path = challenge.file_path(name, 'problem.props')
        if not os.path.exists(props_path):
            raise ObjectDoesNotExist("No such Problem: no such file: {}".format(props_path))
        self._challenge = challenge
        self._name = name

    def __hash__(self):
        return hash(self._name)

    def __eq__(self, other):
        return other._name == self._name

    def __lt__(self, other):
        return (self.difficulty, self.title) < (other.difficulty, other.title)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Problem: {} in {!r}>'.format(self, self.challenge)

    def file_path(self, *tail):
        return self._challenge.file_path(self._name, *tail)

    def _get_properties(self):
        return read_props(self.file_path('problem.props'))
    properties = lazy_attr('_properties_', _get_properties)

    def _get_subject(self):
        subject_path_md = self.file_path('subject.md')
        subject_path_txt = self.file_path('subject.txt')
        if os.path.exists(subject_path_md):
            return open_try_hard(lambda f: f.read(), subject_path_md), 'markdown'
        elif os.path.exists(subject_path_txt):
            return open_try_hard(lambda f: f.read(), subject_path_txt), 'html'
    subject = lazy_attr('_subject_', _get_subject)

    def _get_tests(self):
        tests = {}
        for item in os.listdir(self.file_path()):
            full_path = self.file_path(item)
            if item.endswith('.in') or item.endswith('.out'):
                def store_item(f):
                    tests[item] = f.read()
                open_try_hard(store_item, full_path)
        return tests
    tests = lazy_attr('_tests_', _get_tests)

    def _get_correction_tests(self):
        perf_tests = set(self.performance_tests)
        return sorted(test for test in set(test.split('.', 1)[0] for test in self.tests) if test not in perf_tests)
    correction_tests = lazy_attr('_correction_tests_', _get_correction_tests)

    def _get_performance_tests(self):
        return str(self.properties.get('performance', '')).split()
    performance_tests = lazy_attr('_performance_tests_', _get_performance_tests)

    def _get_language_templates(self):
        templates = {}
        if not os.path.exists(self.file_path('skeleton')):
            return templates
        for item in os.listdir(self.file_path('skeleton')):
            full_path = self.file_path('skeleton', item)
            try:
                base_name, ext = os.path.splitext(os.path.basename(full_path))
            except ValueError:
                # unpacking error
                continue
            if base_name != self.name:
                # not a template
                continue
            lang = Language.guess(ext)
            if lang is None:
                # unknown extension
                continue
            def store_item(f):
                templates[lang] = f.read()
            open_try_hard(store_item, full_path)
        return templates
    language_templates = lazy_attr('_language_templates_', _get_language_templates)

    @property
    def challenge(self):
        return self._challenge

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return str(self.properties.get('title', ''))

    @property
    def difficulty(self):
        return self.properties.get('difficulty', 0)

    @property
    def percentage_difficulty(self):
        return int(self.difficulty / settings.PROLOGIN_MAX_LEVEL_DIFFICULTY * 100)

    @property
    def subject_html(self):
        content, type = self.subject
        if type == 'html':
            return content

    @property
    def subject_markdown(self):
        content, type = self.subject
        if type == 'markdown':
            return content

    def _get_samples(self):
        samples = []
        for sample in str(self.properties.get('samples', '')).split():
            try:
                sample_in = open_try_hard(lambda f: f.read(), self.file_path(sample) + '.in')
                sample_out = open_try_hard(lambda f: f.read(), self.file_path(sample) + '.out')
                sample_comment = ''
                try:
                    sample_comment = open_try_hard(lambda f: f.read(), self.file_path(sample) + '.comment')
                except IOError:
                    pass
                samples.append(Problem.Sample(sample_in, sample_out, sample_comment))
            except IOError:
                pass
        return samples
    samples = lazy_attr('_samples_', _get_samples)
