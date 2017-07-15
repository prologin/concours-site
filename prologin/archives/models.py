import logging
import os
import redis, redis.exceptions
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

import contest.models
import problems.models
import qcm.models
from archives.thirdparty.flickr import Flickr
from archives.thirdparty.vimeo import Vimeo
from prologin.utils import lazy_attr, open_try_hard
from prologin.utils.scoring import Scoreboard

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


class QualificationArchive(WithChallengeMixin, BaseArchive):
    """
    Qualification archive. May have:
        - a challenge
        - a PDF statement
        - a PDF correction
        - a PDF challenge
    """
    dir_name = 'questionnaire'
    event_type = contest.models.Event.Type.qualification

    pdf_statement = lazy_attr('_pdf_statement_', BaseArchive.file_url_or_none('questionnaire.pdf'))
    pdf_correction = lazy_attr('_pdf_correction_', BaseArchive.file_url_or_none('correction.pdf'))
    pdf_challenges = lazy_attr('_pdf_challenges_', BaseArchive.file_url_or_none('challenges.pdf'))

    @property
    def quiz(self) -> qcm.models.Qcm:
        return self.archive.qcm

    def populated(self):
        return any((self.pdf_statement, self.pdf_correction, self.pdf_challenges, self.quiz, self.challenge))


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
        - a flickr photo list
    """
    dir_name = 'finale'

    def _get_scoreboard(self):
        def reader(file):
            return file.readlines()

        def scoreboard_gen():
            lines = open_try_hard(reader, self.file_path('HallOfFame'))
            # pseudo_score so that decorate_with_rank can compute the rank with ties
            pseudo_score = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('#'):
                    continue
                if line.lower().startswith('[tie]'):
                    # don't change the score when there is a tie
                    _, line = line.split('[tie]', 1)
                    line = line.strip()
                else:
                    pseudo_score -= 1
                name, *extra = line.split('(', 1)
                particle = name.split()[0]
                if particle.endswith('.'):
                    name = '{} {}'.format(particle.capitalize().strip(), name.split('.', 1)[1].strip())
                extra = ' '.join(p.strip().strip('()').strip() for p in extra)
                yield {'name': name.strip().title(), 'extra': extra, 'score': pseudo_score}

        try:
            return Scoreboard(scoreboard_gen())
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
    def _qcm_queryset(cls):
        return (qcm.models.Qcm.objects
                .filter(event__type=contest.models.Event.Type.qualification.value))

    @classmethod
    def all_archives(cls):
        qcm_by_year = {qcm.event.edition.year: qcm for qcm in cls._qcm_queryset()}

        def explore():
            for year_dir in os.listdir(settings.ARCHIVES_REPOSITORY_PATH):
                if year_dir.isnumeric():
                    year = int(year_dir)
                    yield Archive(year, qcm_by_year.get(year))

        return explore()

    @classmethod
    def by_year(cls, year: int):
        qcm_obj = cls._qcm_queryset().filter(event__edition__year=year).first()
        return Archive(year, qcm_obj)

    def __init__(self, year: int, qcm_obj: qcm.models.Qcm):
        self.year = year
        self.qcm = qcm_obj

        if not os.path.exists(self.file_path()):
            raise ObjectDoesNotExist("Archive for year {} does not exist".format(year))

        self.photo_collection_url = None
        self.photo_cover_url = None
        self.photo_count = 0
        self.video_id = None
        self.video_picture_id = None
        try:
            self._populate_redis_attributes()
        except redis.exceptions.RedisError:
            pass

    def _populate_redis_attributes(self):
        decode = lambda d: d if d is None else d.decode()
        store = redis.StrictRedis(**settings.PROLOGIN_UTILITY_REDIS_STORE)
        pipe = store.pipeline()
        pipe.get(self.photo_collection_url_key)
        pipe.get(self.photo_cover_url_key)
        pipe.get(self.photo_count_key)
        pipe.get(self.video_id_key)
        pipe.get(self.video_picture_id_key)
        (self.photo_collection_url, cover_url, photo_count, self.video_id, self.video_picture_id,
        ) = map(decode, pipe.execute())
        if cover_url:
            # format with size 's' (small square)
            self.photo_cover_url = Flickr.photo_url_format(cover_url, 's')
        if photo_count:
            self.photo_count = int(photo_count)

    def file_path(self, *tail) -> str:
        return os.path.abspath(os.path.join(settings.ARCHIVES_REPOSITORY_PATH, self.file_url(*tail)))

    def file_url(self, *tail) -> str:
        return os.path.join(str(self.year), *tail)

    def _redis_key(self, suffix):
        return settings.ARCHIVES_REDIS_KEY.format(year=self.year, suffix=suffix)

    @property
    def photo_count_key(self):
        return self._redis_key('photos.count')

    @property
    def photo_collection_url_key(self):
        return self._redis_key('photos.url')

    @property
    def photo_cover_url_key(self):
        return self._redis_key('photos.cover.url')

    @property
    def video_id_key(self):
        return self._redis_key('video.id')

    @property
    def video_picture_id_key(self):
        return self._redis_key('video.picture.id')

    @property
    def video_embed_code(self):
        if not self.video_id:
            return
        return Vimeo.video_embed_code(self.video_id, width="100%", height=300)

    @property
    def video_cover_url(self):
        return Vimeo.video_cover_url(self.video_picture_id, size=48)

    @property
    def video_url(self):
        if not self.video_id:
            return
        return Vimeo.video_url(self.video_id)

    qualification = subtype_factory('_qualification_', QualificationArchive)
    semifinal = subtype_factory('_semifinal_', SemifinalArchive)
    final = subtype_factory('_final_', FinalArchive)

    poster_full = get_poster_factory('full')
    poster_thumb = get_poster_factory('thumb')

    def __repr__(self):
        return "<Archive for {}>".format(self)

    def __str__(self):
        return "Prologin {}".format(self.year)

    def __hash__(self):
        return hash(self.year)

    def __eq__(self, other):
        return other.year == self.year

    def __lt__(self, other):
        return self.year.__lt__(other.year)

    def has_qualification(self):
        return self.qualification
