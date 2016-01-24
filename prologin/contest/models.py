import collections
import itertools
import random
from adminsortable.models import SortableMixin
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Count, Q
from django.db.models.aggregates import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.utils.translation import ugettext_noop, ugettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from jsonfield import JSONField

from centers.models import Center
from prologin.models import EnumField, CodingLanguageField
from prologin.utils import ChoiceEnum, save_random_state


class Edition(ExportModelOperationsMixin('edition'), models.Model):
    year = models.PositiveIntegerField(primary_key=True)
    date_begin = models.DateTimeField()
    date_end = models.DateTimeField()

    qualification_corrected = models.BooleanField(default=False)
    semifinal_corrected = models.BooleanField(default=False)
    final_corrected = models.BooleanField(default=False)

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
        ugettext_noop("Qualification")
        ugettext_noop("Semifinal")
        ugettext_noop("Final")

    edition = models.ForeignKey(Edition, related_name='events')
    center = models.ForeignKey(Center, blank=True, null=True, related_name='events')
    type = EnumField(Type, db_index=True)
    date_begin = models.DateTimeField(blank=True, null=True)
    date_end = models.DateTimeField(blank=True, null=True)

    objects = EventManager()

    class Meta:
        ordering = ('date_begin',)

    @classmethod
    def semifinals_for_edition(cls, year: int):
        return cls.objects.select_related('center').filter(edition__year=year, type=cls.Type.semifinal.value)

    @classmethod
    def final_for_edition(cls, year: int):
        return cls.objects.select_related('center').get(edition__year=year, type=cls.Type.final.value)

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

    @property
    def short_description(self):
        return "{} – {}".format(self.center.name, date_format(self.date_begin, "SHORT_DATE_FORMAT"))

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


class ContestantCompleteSemifinalManager(models.Manager):
    def get_queryset(self):
        return (super().get_queryset()
                .select_related('user', 'assignation_semifinal_event', 'assignation_semifinal_event__center')
                .filter(assignation_semifinal_wishes__type=Event.Type.semifinal.value)
                .annotate(wish_count=Count('assignation_semifinal_wishes', distinct=True))
                .filter(wish_count__gte=settings.PROLOGIN_SEMIFINAL_MIN_WISH_COUNT)
                .exclude(
                    Q(preferred_language__isnull=True) |
                    Q(user__first_name__exact='') |
                    Q(user__last_name__exact='') |
                    Q(user__address__exact='') |
                    Q(user__postal_code__exact='') |
                    Q(user__city__exact='') |
                    Q(user__country__exact='')
                ))


@ChoiceEnum.labels(str.upper)
class ShirtSize(ChoiceEnum):
    xs = 0
    s = 1
    m = 2
    l = 3
    xl = 4
    xxl = 5


@ChoiceEnum.labels(lambda lbl: lbl.replace('_', ' ').capitalize())
class Assignation(ChoiceEnum):
    not_assigned = 0
    ruled_out = 1
    assigned = 2
    ugettext_noop("Not assigned")
    ugettext_noop("Ruled out")
    ugettext_noop("Assigned")


class Contestant(ExportModelOperationsMixin('contestant'), models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='contestants')
    edition = models.ForeignKey(Edition, related_name='contestants')

    shirt_size = EnumField(ShirtSize, null=True, blank=True, db_index=True,
                           verbose_name=_("T-shirt size"), empty_label=_("Choose your size"),
                           help_text=_("We usually provide unisex Prologin t-shirts to the finalists."))
    preferred_language = CodingLanguageField(null=True, blank=True, db_index=True,
                                             help_text=_("The programming language you will most likely use during the "
                                                         "regional events."))

    assignation_semifinal = EnumField(Assignation, default=Assignation.not_assigned.value,
                                      verbose_name=_("Semifinal assignation status"))
    assignation_semifinal_wishes = models.ManyToManyField(Event, through='EventWish',
                                                          related_name='applicants', blank=True,
                                                          verbose_name=_("Semifinal assignation whishes"))
    assignation_semifinal_event = models.ForeignKey(Event, related_name='assigned_contestants', blank=True, null=True,
                                                    verbose_name=_("Semifinal assigned event"))
    assignation_final = EnumField(Assignation, default=Assignation.not_assigned.value,
                                  verbose_name=_("Final assignation status"))

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
    complete_for_semifinal = ContestantCompleteSemifinalManager()

    class Meta:
        unique_together = ('user', 'edition')

    def get_score_fields_for_type(self, type: Event.Type) -> dict:
        mapping = {Event.Type.qualification: 'qualif'}
        return collections.OrderedDict([
            (field, getattr(self, field.name))
            for field in self._meta.get_fields()
            if field.name.startswith('score_{}_'.format(mapping.get(type, type.name)))
        ])

    @property
    def _is_complete(self):
        # update ContestantManager.complete_for_{,semi}final accordingly
        return all((self.shirt_size is not None, self.preferred_language, self.user.first_name, self.user.last_name,
                    self.user.address, self.user.postal_code, self.user.city, self.user.country))

    @property
    def _wish_count(self):
        try:
            return self.wish_count
        except AttributeError:
            self.wish_count = (self.assignation_semifinal_wishes
                               .filter(type=Event.Type.semifinal.value).distinct().count())
            return self.wish_count

    @property
    def is_complete_for_semifinal(self):
        # update ContestantManager.complete_for_semifinal accordingly
        if self._wish_count < settings.PROLOGIN_SEMIFINAL_MIN_WISH_COUNT:
            return False
        return self._is_complete

    @property
    def is_assigned_for_semifinal(self):
        return self.assignation_semifinal == Assignation.assigned.value

    @property
    def is_ruled_out_for_semifinal(self):
        return self.assignation_semifinal == Assignation.ruled_out.value

    @property
    def is_assigned_for_final(self):
        return self.assignation_final == Assignation.assigned.value

    @property
    def is_ruled_out_for_final(self):
        return self.assignation_final == Assignation.ruled_out.value

    @property
    def is_complete_for_finale(self):
        return self._is_complete

    def score_for(self, event_type: Event.Type):
        return sum(score or 0 for score in self.get_score_fields_for_type(event_type).values())

    @property
    def score_for_qualification(self):
        return self.score_for(Event.Type.qualification)

    @property
    def score_for_semifinal(self):
        return self.score_for(Event.Type.semifinal)

    @property
    def assignation_final_event(self):
        return Event.objects.get(edition=self.edition, type=Event.Type.final.value)

    @property
    def total_score(self):
        return sum(getattr(self, name) or 0
                   for name in self._meta.get_all_field_names()
                   if name.startswith('score_'))

    @cached_property
    def semifinal_challenge(self):
        from problems.models import Challenge
        return Challenge.by_year_and_event_type(self.edition.year, Event.Type.semifinal)

    @cached_property
    def semifinal_explicitly_unlocked_problems(self):
        from problems.models import ExplicitProblemUnlock
        return ExplicitProblemUnlock.objects.filter(challenge=self.semifinal_challenge.name, user=self.user)

    @cached_property
    def semifinal_lines_of_code(self):
        from problems.models import SubmissionCode
        return sum(1
                   for code in (SubmissionCode.objects
                                .filter(submission__user=self.user,
                                        submission__challenge=self.semifinal_challenge.name)
                                .values_list('code', flat=True))
                   for line in code.replace('\r', '\n').split('\n') if line.strip())

    @cached_property
    def semifinal_problems_score(self):
        from problems.models import Submission
        return (Submission.objects
                .filter(user=self.user, challenge=self.semifinal_challenge.name)
                .aggregate(score=Coalesce(Sum('score_base') - Sum('malus'), 0))).score

    @cached_property
    def available_semifinal_problems(self):
        from problems.models import Challenge, Submission, ExplicitProblemUnlock
        challenge = self.semifinal_challenge

        if self.user.is_staff:
            return list(challenge.problems)

        elif challenge.type == Challenge.Type.standard:
            return list(challenge.problems)

        seed = self.user.pk
        problem_to_solved_date = {}
        problem_to_unlock_date = {}
        difficulty_to_solved = collections.defaultdict(set)

        for unlock in ExplicitProblemUnlock.objects.filter(user=self.user, challenge=challenge.name):
            problem = challenge.problem(unlock.problem)
            problem_to_unlock_date[problem] = unlock.date_created

        for submission in Submission.objects.filter(user=self.user, challenge=challenge.name, score_base__gt=0):
            problem = challenge.problem(submission.problem)
            problem_to_solved_date[problem] = submission.first_code_success().date_submitted
            difficulty_to_solved[problem.difficulty].add(problem)

        # transform into real dict, so we don't get an empty set but an actual KeyError on missing keys
        difficulty_to_solved = dict(difficulty_to_solved)

        dl = challenge.problem_difficulty_list
        for previous_difficulty, difficulty in itertools.zip_longest(dl, dl[1:]):
            problems = challenge.problems_of_difficulty(difficulty)

            try:
                earliest_unlock_date = min(problem_to_solved_date[problem]
                                           for problem in difficulty_to_solved[previous_difficulty])
            except KeyError:
                # no solved problems of previous_difficulty
                earliest_unlock_date = None

            if challenge.type == Challenge.Type.all_per_level:
                if earliest_unlock_date:
                    for problem in problems:
                        problem_to_unlock_date[problem] = earliest_unlock_date

            elif challenge.type == Challenge.Type.one_per_level:
                if earliest_unlock_date:
                    with save_random_state(seed):
                        problem_to_unlock_date[random.choice(problems)] = earliest_unlock_date

            elif challenge.type == Challenge.Type.one_per_level_delayed:
                # number of solved problems of previous_difficulty
                quantity = len(difficulty_to_solved.get(previous_difficulty, []))
                # unlock (number of solved previous_difficulty) problems of difficulty
                quantity = min(quantity, len(problems))
                if quantity:
                    with save_random_state(seed):
                        for problem in random.sample(problems, quantity):
                            problem_to_unlock_date[problem] = earliest_unlock_date
                # unlock a single previous-difficulty problem if still no success at this difficulty
                if earliest_unlock_date and not difficulty_to_solved.get(difficulty):
                    # previous-difficulty problems that are not already unlocked
                    previous_difficulty_problems = [problem for problem in challenge.problems_of_difficulty(previous_difficulty)
                                                    if problem not in problem_to_unlock_date]
                    if previous_difficulty_problems:
                        if (timezone.now() - earliest_unlock_date).seconds > challenge.auto_unlock_delay:
                            # waited long enough, unlock a new previous-difficulty problem
                            with save_random_state(seed):
                                problem = random.choice(previous_difficulty_problems)
                                problem_to_unlock_date[problem] = earliest_unlock_date

        # should not happen, but you never know (eg. if explicit unlock is removed after it's solved)
        # assign a fake unlock date to problems that are solved but not unlocked (wtf)
        for problem, solved_date in problem_to_solved_date.items():
            if problem not in problem_to_unlock_date:
                problem_to_unlock_date[problem] = solved_date

        return {problem: {'unlocked': date_unlocked,
                          'solved': problem_to_solved_date.get(problem)}
                for problem, date_unlocked in problem_to_unlock_date.items()}

    def compute_changes(self, new, event_type):
        changes = {
            field.name: getattr(new, field.name)
            for field, value in new.get_score_fields_for_type(event_type).items()
            if getattr(self, field.name) != value
        }
        if event_type == Event.Type.qualification:
            if self.assignation_semifinal != new.assignation_semifinal:
                changes['assignation_semifinal'] = new.assignation_semifinal
            if self.assignation_semifinal_event != new.assignation_semifinal_event:
                changes['assignation_semifinal_event'] = (new.assignation_semifinal_event.pk
                                                          if new.assignation_semifinal_event else None)
        elif event_type == Event.Type.semifinal:
            if self.assignation_final != new.assignation_final:
                changes['assignation_final'] = new.assignation_final
        return changes

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
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='contestant_correction', null=True, blank=True)
    comment = models.TextField(blank=True)
    event_type = EnumField(Event.Type, db_index=True)
    changes = JSONField(blank=True)
    date_created = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        get_latest_by = 'date_created'
        ordering = ('-' + get_latest_by,)

    @property
    def date_created_utc(self):
        return int(timezone.make_naive(self.date_created, timezone.utc).timestamp())

    def get_changes(self, precision='0.01'):
        precision = Decimal(precision)
        event_type = Event.Type(self.event_type)

        def get_event_description(value):
            return Event.objects.select_related('center').get(pk=value).short_description

        def build():
            for field in self.contestant.get_score_fields_for_type(event_type):
                try:
                    value = self.changes[field.name]
                except KeyError:
                    continue
                yield {
                    'field': field,
                    'type': 'score',
                    'value': None if value is None else Decimal(value).quantize(precision),
                }

            for enum in ('assignation_semifinal', 'assignation_final'):
                try:
                    value = self.changes[enum]
                except KeyError:
                    continue

                yield {
                    'field': Contestant._meta.get_field(enum),
                    'type': 'enum',
                    'value': Assignation.label_for(Assignation(value)),
                }

            for nullable, getter in (('assignation_semifinal_event', get_event_description),):
                try:
                    value = self.changes[nullable]
                except KeyError:
                    continue
                if value is not None:
                    try:
                        value = getter(value)
                    except Exception:
                        continue
                yield {
                    'field': Contestant._meta.get_field(nullable),
                    'type': 'nullable',
                    'value': value,
                }

        return list(build())
