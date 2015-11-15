import os
from collections import namedtuple
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

import contest.models
import problems.models
import qcm.models
from prologin.utils import lazy_attr, open_try_hard


class BaseArchive:
    """
    Abstract class for {Qualification,Semifinal,Final}Archive.
    """
    dir_name = None
    event_type = None

    def __init__(self, archive):
        self.archive = archive

    def file_path(self, *tail) -> str:
        return self.archive.file_path(self.dir_name, *tail)

    def file_url(self, *tail) -> str:
        return os.path.join(settings.ARCHIVES_REPOSITORY_STATIC_PREFIX, self.archive.file_url(self.dir_name, *tail))

    @classmethod
    def file_url_or_none(cls, *tail) -> str:
        def func(self):
            path = self.file_path(*tail)
            if os.path.exists(path):
                return self.file_url(*tail)
            return None

        return func

    def populated(self):
        raise NotImplementedError("BaseArchive subclasses has to implement populated()")

    def __repr__(self):
        return "<{} for {}{}>".format(self.__class__.__name__,
                                      self.archive.year,
                                      '' if self.populated() else ' (empty)')


class WithChallengeMixin:
    """
    Mixin for archive types that have a problems.Challenge (qualification, semifinal).
    """
    event_type = None

    @property
    def challenge(self) -> problems.models.Challenge:
        try:
            return problems.models.Challenge.by_year_and_event_type(self.archive.year, self.event_type)
        except ObjectDoesNotExist:
            return None


class WithContentMixin:
    """
    Mixin for archive types that have a content (semifinal, final).
    """

    def _get_content(self):
        def callback(obj):
            # TODO: parse the weird shit format
            return mark_safe(obj.read())

        try:
            return open_try_hard(callback, self.file_path('content.html'))
        except (ValueError, FileNotFoundError):
            return None

    content = lazy_attr('_content_', _get_content)


class QualificationArchive(WithChallengeMixin, BaseArchive):
    """
    Qualification archive. May have:
        - a challenge
        - a PDF statement
        - a PDF correction
    """
    dir_name = 'questionnaire'
    event_type = contest.models.Event.Type.qualification

    pdf_statement = lazy_attr('_pdf_statement_', BaseArchive.file_url_or_none('questionnaire.pdf'))
    pdf_correction = lazy_attr('_pdf_correction_', BaseArchive.file_url_or_none('correction.pdf'))

    @property
    def quiz(self) -> qcm.models.Qcm:
        return qcm.models.Qcm.objects.filter(event__edition__year=self.archive.year, event__type=self.event_type.value).first()

    def populated(self):
        return any((self.pdf_statement, self.pdf_correction, self.quiz, self.challenge))


class SemifinalArchive(WithContentMixin, WithChallengeMixin, BaseArchive):
    """
    Semifinal archive. May have:
        - a challenge
        - a content
    """
    dir_name = 'demi-finales'
    event_type = contest.models.Event.Type.semifinal

    def populated(self):
        return any((self.content, self.challenge))


class FinalArchive(WithContentMixin, BaseArchive):
    """
    Final archive. May have:
        - a content
        - a scoreboard
    """
    dir_name = 'finale'

    ScoreboardItem = namedtuple('ScoreboardItem', 'name extra')

    def _get_scoreboard(self):
        def reader(file):
            return file.readlines()

        def generator():
            lines = open_try_hard(reader, self.file_path('HallOfFame'))
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                name, *extra = line.split('(', 1)
                particle = name.split()[0]
                if particle.endswith('.'):
                    name = '{} {}'.format(particle.capitalize().strip(), name.split('.', 1)[1].strip())
                extra = ' '.join(p.strip().strip('()').strip() for p in extra)
                yield FinalArchive.ScoreboardItem(name=name.strip().title(), extra=extra)

        try:
            return list(generator())
        except FileNotFoundError:
            return None

    scoreboard = lazy_attr('_scoreboard_', _get_scoreboard)

    def populated(self):
        return any((self.content, self.scoreboard))


def subtype_factory(prop_name, cls):
    assert issubclass(cls, BaseArchive)

    def builder(self):
        return cls(self)

    return lazy_attr(prop_name, builder)


def get_poster_factory(size):
    name = 'poster_{}.jpg'.format(size)

    def getter(self):
        path = self.file_path(name)
        if os.path.exists(path):
            return os.path.join(settings.ARCHIVES_REPOSITORY_STATIC_PREFIX, self.file_url(name))
        return None

    return lazy_attr('_poster_{}_'.format(size), getter)


class Archive:
    """
    Root archive class for a given year.

    Use Archive.all_archives() to list all archives (result is sortable).
    Use Archive.by_year(year) to retrieve a specific year archive.

    Each Archive instance may have:
        - a big poster URL
        - a small poster URL

    Each Archive instance has the following attributes to access the respective event-archive instance:
        - qualification
        - semifinal
        - final
    """

    @classmethod
    def all_archives(cls):
        def explore():
            for year_dir in os.listdir(settings.ARCHIVES_REPOSITORY_PATH):
                try:
                    yield Archive(int(year_dir))
                except Exception:
                    pass

        return explore()

    @classmethod
    def by_year(cls, year: int):
        return Archive(year)

    def __init__(self, year: int):
        self.year = year
        if not os.path.exists(self.file_path()):
            raise ObjectDoesNotExist("Archive for year {} does not exist".format(year))

    def file_path(self, *tail) -> str:
        return os.path.abspath(os.path.join(settings.ARCHIVES_REPOSITORY_PATH, self.file_url(*tail)))

    def file_url(self, *tail) -> str:
        return os.path.join(str(self.year), *tail)

    qualification = subtype_factory('_qualification_', QualificationArchive)
    semifinal = subtype_factory('_semifinal_', SemifinalArchive)
    final = subtype_factory('_final_', FinalArchive)

    poster_big = get_poster_factory('big')
    poster_small = get_poster_factory('small')

    def __repr__(self):
        return "<Archive for {}>".format(self.year)

    def __hash__(self):
        return hash(self.year)

    def __eq__(self, other):
        return other.year == self.year

    def __lt__(self, other):
        return self.year.__lt__(other.year)

    def has_qualification(self):
        return self.qualification
