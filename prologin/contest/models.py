from adminsortable.models import SortableMixin
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_noop, ugettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from jsonfield import JSONField

from centers.models import Center
from prologin.models import EnumField, CodingLanguageField
from prologin.utils import ChoiceEnum


class Edition(ExportModelOperationsMixin('edition'), models.Model):
    year = models.PositiveIntegerField(primary_key=True)
    date_begin = models.DateTimeField()
    date_end = models.DateTimeField()

    class Meta:
        ordering = ('-year',)

    @property
    def is_active(self):
        return self.date_begin <= timezone.now() <= self.date_end

    def __str__(self):
        return "Prologin {}".format(self.year)


class EventManager(models.Manager):
    def get_queryset(self):
        return (super().get_queryset()
                .select_related('edition', 'center'))


class Event(ExportModelOperationsMixin('event'), models.Model):
    @ChoiceEnum.labels(str.capitalize)
    class Type(ChoiceEnum):
        qualification = 0
        semifinal = 1
        final = 2
        ugettext_noop("Qualifications")
        ugettext_noop("Semifinal")
        ugettext_noop("Final")

    edition = models.ForeignKey(Edition, related_name='events')
    center = models.ForeignKey(Center, blank=True, null=True, related_name='events')
    type = EnumField(Type, db_index=True)
    date_begin = models.DateTimeField(blank=True, null=True)
    date_end = models.DateTimeField(blank=True, null=True)

    objects = EventManager()

    @property
    def is_finished(self):
        return self.date_end < timezone.now()

    @property
    def is_in_future(self):
        return timezone.now() < self.date_begin

    @property
    def is_active(self):
        return self.date_begin <= timezone.now() <= self.date_end

    @property
    def challenge(self):
        from problems.models import Challenge  # circular import
        try:
            return Challenge.by_year_and_event_type(self.edition.year, Event.Type(self.type))
        except ObjectDoesNotExist:
            return None

    def __str__(self):
        return "{edition}: {type} starting {starting}{at}".format(
            edition=self.edition,
            type=self.get_type_display(),
            starting=self.date_begin,
            at=" at %s" % self.center if self.center else "",
        )


class ContestantManager(models.Manager):
    def get_queryset(self):
        return (super().get_queryset()
                .select_related('edition', 'user'))


@ChoiceEnum.labels(str.upper)
class ShirtSize(ChoiceEnum):
    xs = 0
    s = 1
    m = 2
    l = 3
    xl = 4
    xxl = 5


class Contestant(ExportModelOperationsMixin('contestant'), models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='contestants')
    edition = models.ForeignKey(Edition, related_name='contestants')
    event_wishes = models.ManyToManyField(Event, through='EventWish', related_name='applicants', blank=True)
    assigned_event = models.ForeignKey(Event, related_name='assigned_contestants', blank=True, null=True)

    shirt_size = EnumField(ShirtSize, null=True, blank=True, db_index=True,
                           verbose_name=_("T-shirt size"), empty_label=_("Choose your size"),
                           help_text=_("We usually provide unisex Prologin t-shirts to the finalists."))
    preferred_language = CodingLanguageField(null=True, blank=True, db_index=True,
                                             help_text=_("The programming language you will most likely use during the "
                                                         "regional events."))

    score_qualif_qcm = models.IntegerField(blank=True, null=True, verbose_name=_("Quiz score"))
    score_qualif_algo = models.IntegerField(blank=True, null=True, verbose_name=_("Algo exercises score"))
    score_qualif_bonus = models.IntegerField(blank=True, null=True, verbose_name=_("Bonus score"))
    score_semifinal_written = models.IntegerField(blank=True, null=True, verbose_name=_("Written exam score"))
    score_semifinal_interview = models.IntegerField(blank=True, null=True, verbose_name=_("Interview score"))
    score_semifinal_machine = models.IntegerField(blank=True, null=True, verbose_name=_("Machine exam score"))
    score_semifinal_bonus = models.IntegerField(blank=True, null=True, verbose_name=_("Bonus score"))
    score_final = models.IntegerField(blank=True, null=True, verbose_name=_("Score"))
    score_final_bonus = models.IntegerField(blank=True, null=True, verbose_name=_("Bonus score"))

    objects = ContestantManager()

    class Meta:
        unique_together = ('user', 'edition')

    @property
    def _is_complete(self):
        return all((self.shirt_size is not None, self.preferred_language, self.user.first_name, self.user.last_name,
                    self.user.address, self.user.postal_code, self.user.city, self.user.country))

    @property
    def is_complete_for_semifinal(self):
        if self.event_wishes.filter(type=Event.Type.semifinal.value).distinct().count() < settings.PROLOGIN_SEMIFINAL_MIN_WISH_COUNT:
            return False
        return self._is_complete

    @property
    def is_complete_for_finale(self):
        return self._is_complete

    @property
    def total_score(self):
        return sum(getattr(self, name) or 0
                   for name in self._meta.get_all_field_names()
                   if name.startswith('score_'))

    def __str__(self):
        return "{edition}: {user}".format(user=self.user, edition=self.edition)


class EventWish(ExportModelOperationsMixin('event_wish'), SortableMixin):
    contestant = models.ForeignKey(Contestant)
    event = models.ForeignKey(Event)
    order = models.IntegerField(editable=False, db_index=True)

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return "{edition}: {who} to go to {where}".format(
            edition=self.event.edition,
            who=self.contestant.user,
            where=self.event.center,
        )


class ContestantCorrection(ExportModelOperationsMixin('contestant_correction'), models.Model):
    contestant = models.ForeignKey(Contestant, related_name='corrections')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='correction_comments', null=True, blank=True)
    comment = models.TextField(blank=True)
    event_type = EnumField(Event.Type, db_index=True)
    changes = JSONField(blank=True)
    date_added = models.DateTimeField(default=timezone.now)
