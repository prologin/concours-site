import os

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Max
from django.utils.functional import cached_property

from centers.models import Center
from prologin.models import EnumField
from prologin.utils import ChoiceEnum


class Edition(models.Model):
    year = models.PositiveIntegerField(primary_key=True)

    @cached_property
    def poster_url(self):
        """Gets poster's url if it exists else return None"""
        name = 'poster.full.jpg'
        path = self.file_path(name)
        if os.path.exists(path):
            return self.file_url(name)


    def file_path(self, *tail):
        """Gets file's absolute path"""
        return os.path.abspath(
            os.path.join(
                settings.GCC_REPOSITORY_PATH,
                str(self.year), *tail
            )
        )

    def file_url(self, *tail):
        """Gets file's url"""
        return os.path.join(
            settings.STATIC_URL, settings.GCC_REPOSITORY_STATIC_PREFIX,
            str(self.year), *tail
        )

    def __str__(self):
        return str(self.year)


class Event(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    event_start = models.DateField()
    event_end = models.DateField()
    signup_start = models.DateField()
    signup_end = models.DateField()

    def __str__(self):
        return str(self.event_start) + ' ' + str(self.center)


class Corrector(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)


class ApplicantLabel(models.Model):
    """Labels to comment on an applicant"""
    display = models.CharField(max_length=10)

    def __str__(self):
        return self.display


@ChoiceEnum.labels(str.capitalize)
class ApplicantStatusTypes(ChoiceEnum):
    pending = 0  # the candidate hasn't finished her registration yet
    rejected = 1  # the candidate's application has been rejected
    selected = 2  # the candidate has been selected for participation
    accepted = 3  # the candidate has been assigned to an event and emailed
    confirmed = 4  # the candidate confirmed her participation


class Applicant(models.Model):
    """
    An applicant for a specific edition and reviews about him.

    Notice that no free writting field has been added yet in order to ensure an
    RGPD-safe usage of reviews.
    """
    # General informations about the application
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    status = EnumField(ApplicantStatusTypes)

    # Whishes of the candidate
    assignation_wishes = models.ManyToManyField(
        Event, through='EventWish', related_name='applicants', blank=True)
    assignation_event = models.ForeignKey(
        Event, related_name='assigned_girls', null=True,
        on_delete=models.SET_NULL)

    # Review of the application
    labels = models.ManyToManyField(ApplicantLabel)

    def for_user(user):
        """
        Get applicant object corresponding to an user for current edition. If no
        applicant has been created for this edition yet, it will be created.
        """
        edition = Edition.objects.latest('year')

        try:
            return Applicant.objects.get(user=user, edition=edition)
        except Applicant.DoesNotExist:
            applicant = Applicant(
                user = user,
                edition = edition,
                status = ApplicantStatusTypes.pending.value
            )
            applicant.save()
            return applicant

    class AlreadyLocked(Exception):
        """
        This exception is raised if a new application is submitted for an user
        who has already been accepted or rejected this year.
        """
        pass

    class Meta:
        unique_together = (('user', 'edition'), )


class EventWish(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    # Priority defined by the candidate to express his prefered event
    # The lower the order is, the more important is the choice
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ('order', )
        unique_together = (('applicant', 'event'), )

    def __str__(self):
        return '{} for {} ({})'.format(
            str(self.applicant),
            str(self.event),
            str(self.status)
        )


@ChoiceEnum.labels(str.capitalize)
class Forms(ChoiceEnum):
    application = 0
    profile = 1


@ChoiceEnum.labels(str.capitalize)
class AnswerTypes(ChoiceEnum):
    boolean = 0
    integer = 1
    date = 2
    string = 3
    text = 4


class Question(models.Model):
    # Formulation of the question
    question = models.TextField()
    # Potential additional indications about the questions
    comment = models.TextField(blank=True)
    # The form this question is part of
    form = EnumField(Forms)
    # How to represent the answer
    response_type = EnumField(AnswerTypes)
    # Wether the answer is mandatory or not
    required = models.BooleanField(default=False)
    # Some extra constraints on the answer
    meta = JSONField(encoder=DjangoJSONEncoder, default=dict, null=True)

    def __str__(self):
        return self.question


class Answer(models.Model):
    applicant = models.ForeignKey(Applicant, related_name='answers', on_delete=models.CASCADE, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = JSONField(encoder=DjangoJSONEncoder)

    def __str__(self):
        return self.response

    class Meta:
        unique_together = (('applicant', 'question'), )


class SubscriberEmail(models.Model):
    email = models.EmailField()

    def __str__(self):
        return self.email
