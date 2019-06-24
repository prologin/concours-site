# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import enum
import os
import re
from collections import namedtuple
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from contest.models import Event
from prologin.languages import Language
from prologin.utils import open_try_hard, lazy_attr, read_props

PROBLEM_NAME_PATTERN = r'^[a-z0-9_.-]+$'


class TestType(enum.Enum):
    correction = 'correction'
    performance = 'performance'


class Test:
    def __init__(self, name: str, type: TestType, hidden: bool, stdin: str, stdout: str):
        self.name = name
        self.type = type
        self.hidden = hidden
        self.stdin = stdin
        self.stdout = stdout


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

    def _get_problems_dict(self):
        return {problem.name: problem for problem in self.problems}
    problems_dict = lazy_attr('_problems_dict_', _get_problems_dict)

    def problem(self, name):
        return self.problems_dict[name]

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
        return self.properties.get('display-website', False)

    @property
    def type(self) -> Type:
        return Challenge.Type(self.properties.get('type'))

    @property
    def auto_unlock_delay(self) -> int:
        """
        The amount of seconds to wait before auto-unlocking new problem(s).
        """
        return self.properties.get('unlock-delay', settings.PROBLEMS_DEFAULT_AUTO_UNLOCK_DELAY)

    @property
    def problem_difficulty_list(self) -> [int]:
        """
        Sorted list of problem difficulties for this challenge.
        """
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
        if re.match(PROBLEM_NAME_PATTERN, name) is None:
            raise ObjectDoesNotExist(
                'Invalid problem name "{}": does not match '
                'regular expression {}'
                .format(name, PROBLEM_NAME_PATTERN))
        if not os.path.exists(props_path):
            raise ObjectDoesNotExist("No such Problem: no such file: {}".format(props_path))
        self._challenge = challenge
        self._name = name

    def __hash__(self):
        return hash((self._challenge, self._name))

    def __eq__(self, other):
        return isinstance(other, Problem) and self._challenge == other._challenge and self._name == other._name

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
        tests_in = {}
        tests_out = {}
        for item in os.listdir(self.file_path('test')):
            full_path = self.file_path('test', item)
            if item.endswith('.in') or item.endswith('.out'):
                name = os.path.splitext(item)[0]
                storage = tests_in if item.endswith('.in') else tests_out
                def store_item(f):
                    storage[name] = f.read()
                open_try_hard(store_item, full_path)

        perf = self.performance_tests
        hidden = self.hidden_tests

        def gen():
            for key in sorted(tests_in.keys() & tests_out.keys()):
                yield Test(key, TestType.performance if key in perf else TestType.correction,
                           key in hidden, tests_in[key], tests_out[key])
        return list(gen())
    tests = lazy_attr('_tests_', _get_tests)

    def _get_hidden_tests(self):
        return set(str(self.properties.get('hidden', '')).split())
    hidden_tests = lazy_attr('_hidden_tests_', _get_hidden_tests)

    def _get_correction_tests(self):
        perf_tests = set(self.performance_tests)
        return sorted(test for test in set(test.rsplit('.', 1)[0] for test in self.tests) if test not in perf_tests)
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
    def stop_early(self):
        return self.properties.get('stop-early', True)

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

    def execution_limits(self, language: Language):
        langdef = language.value
        limits = {'fsize': 4000}
        mem_limit = self.properties.get('mem')
        if mem_limit:
            limits['mem'] = langdef.memory_limit(mem_limit)
        time_limit = self.properties.get('time')
        if time_limit:
            limits['time'] = langdef.time_limit(time_limit / 1000.)
            # factor allowing a program to run MAX_REALTIME * ALLOWED if time (ie. user-time) is not reached
            limits['wall-time'] = 3 * limits['time']
        return limits

    def _get_samples(self):
        samples = []
        for sample in str(self.properties.get('samples', '')).split():
            try:
                sample_in = open_try_hard(
                    lambda f: f.read(),
                    self.file_path('test', sample) + '.in')
                sample_out = open_try_hard(
                    lambda f: f.read(),
                    self.file_path('test', sample) + '.out')
                sample_comment = ''
                try:
                    sample_comment = open_try_hard(
                        lambda f: f.read(),
                        self.file_path('test', sample) + '.comment')
                except IOError:
                    pass
                samples.append(Problem.Sample(sample_in, sample_out,
                                              sample_comment))
            except IOError:
                pass
        return samples
    samples = lazy_attr('_samples_', _get_samples)
