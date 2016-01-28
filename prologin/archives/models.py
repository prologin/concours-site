import logging
import os
import random
import redis, redis.exceptions
import yaml
from collections import namedtuple
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

import contest.models
import problems.models
import qcm.models
from archives.flickr import Flickr
from prologin.utils import lazy_attr, open_try_hard

logger = logging.getLogger('prologin.archives')


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
            challenge = problems.models.Challenge.by_year_and_event_type(self.archive.year, self.event_type)
            if hasattr(self.archive, 'user') and not self.archive.user.has_perm('problems.view_challenge', challenge):
                return None
            return challenge
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


class WithFlickrMixin:
    flickr_album_id = None
    flickr_redis_suffix = None

    def get_flickr_album_id(self):
        return self.flickr_album_id

    def get_flickr_photos(self, flickr=None):
        if not flickr:
            flickr = Flickr(*settings.ARCHIVES_FLICKR_CREDENTIALS)
        if self.get_flickr_album_id():
            return list(flickr.photos(self.get_flickr_album_id()))
        else:
            return []

    @property
    def flickr_album_url(self):
        return settings.ARCHIVES_FLICKR_ALBUM_URL.format(id=self.get_flickr_album_id())

    def _flickr_redis_key(self):
        return settings.ARCHIVES_FLICKR_REDIS_KEY.format(year=self.archive.year, suffix=self.flickr_redis_suffix)

    def _get_flickr_thumbs(self):
        if not self.flickr_redis_suffix:
            raise ValueError('`flickr_redis_suffix` can not be empty')
        try:
            store = redis.StrictRedis(**settings.PROLOGIN_UTILITY_REDIS_STORE)
            photos = store.lrange(self._flickr_redis_key(), 0, -1)
            random.shuffle(photos)
            return photos
        except redis.exceptions.RedisError:
            logger.exception("Could not connect to Redis %s to serve archive thumbnails",
                             settings.PROLOGIN_UTILITY_REDIS_STORE)
            return []

    flickr_thumbs = lazy_attr('_flickr_thumbs_', _get_flickr_thumbs)


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
        qcm_obj = qcm.models.Qcm.objects.filter(event__edition__year=self.archive.year, event__type=self.event_type.value).first()
        if qcm_obj and hasattr(self.archive, 'user') and not self.archive.user.has_perm('qcm.view_qcm', qcm_obj):
            return None
        return qcm_obj

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


class FinalArchive(WithFlickrMixin, WithContentMixin, BaseArchive):
    """
    Final archive. May have:
        - a content
        - a scoreboard
        - a flickr photo list
    """
    dir_name = 'finale'
    flickr_redis_suffix = dir_name

    ScoreboardItem = namedtuple('ScoreboardItem', 'name extra')

    def get_flickr_album_id(self):
        def read(file):
            return yaml.load(file.read()).get('flickr-album-id')
        try:
            return open_try_hard(read, self.file_path('event.props'))
        except (FileNotFoundError, yaml.YAMLError):
            return None

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
    name = 'poster.{}.jpg'.format(size)

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
        - a full-size poster URL (.poster_full)
        - a thumbnail-size poster URL (.poster_thumb)

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

    poster_full = get_poster_factory('full')
    poster_thumb = get_poster_factory('thumb')

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
