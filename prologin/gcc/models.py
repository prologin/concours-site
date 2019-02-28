import hashlib
import os
from datetime import date

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.functional import cached_property

from centers.models import Center
from prologin.models import EnumField
from prologin.utils import ChoiceEnum


class Edition(models.Model):
    year = models.PositiveIntegerField(primary_key=True, unique=True)
    signup_form = models.ForeignKey('Form', on_delete=models.CASCADE)

    @cached_property
    def poster_url(self):
        """Gets poster's URL if it exists else return None"""
        name = 'poster.full.jpg'
        path = self.file_path(name)

        if not os.path.exists(path):
            return None

        return self.file_url(name)

    def file_path(self, *tail):
        """Gets file's absolute path"""
        return os.path.abspath(
            os.path.join(settings.GCC_REPOSITORY_PATH, str(self.year), *tail))

    def file_url(self, *tail):
        """Gets file's URL"""
        return os.path.join(
            settings.STATIC_URL, settings.GCC_REPOSITORY_STATIC_PREFIX,
            str(self.year), *tail)

    @staticmethod
    def current():
        """Gets current edition"""
        return Edition.objects.latest()

    def subscription_is_open(self):
        """Is there still one event open for subscription"""
        current_events = Event.objects.filter(edition=self,
                                              signup_start__lt=date.today(),
                                              signup_end__gte=date.today())
        return current_events.exists()

    def user_has_applied(self, user):
        """Check whether a user has applied for this edition"""
        return Applicant.objects.filter(user=user, edition=self).exists()

    def __str__(self):
        return str(self.year)

    class Meta:
        ordering = ['-year']
        get_latest_by = ['year']



class Event(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    event_start = models.DateTimeField()
    event_end = models.DateTimeField()
    signup_start = models.DateTimeField()
    signup_end = models.DateTimeField()
    signup_form = models.ForeignKey('Form', on_delete=models.CASCADE,
                                    null=True)

    def __str__(self):
        return str(self.event_start) + ' ' + str(self.center)

    def short_description(self):
        return '{name} – {start} – {end}'.format(
            name=self.center.name,
            start=date_format(self.event_start, "SHORT_DATE_FORMAT"),
            end=date_format(self.event_end, "SHORT_DATE_FORMAT"))


class Corrector(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE,
                              related_name='correctors')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)


class ApplicantLabel(models.Model):
    """Labels to comment on an applicant"""
    display = models.CharField(max_length=10)

    def __str__(self):
        return self.display


class ApplicantStatusTypes(ChoiceEnum):
    incomplete  = 0  # the candidate hasn't finished her registration yet
    pending     = 1  # the candidate finished here registration
    rejected    = 2  # the candidate's application has been rejected
    selected    = 3  # the candidate has been selected for participation
    accepted    = 4  # the candidate has been assigned to an event and emailed
    confirmed   = 5  # the candidate confirmed her participation


class Applicant(models.Model):
    """
    An applicant for a specific edition and reviews about him.

    Notice that no free writing field has been added yet in order to ensure an
    GDPR-safe usage of reviews.
    """
    # General informations about the application
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    status = EnumField(ApplicantStatusTypes, db_index=True, blank=True,
                       default=ApplicantStatusTypes.incomplete.value)

    # Wishes of the candidate
    assignation_wishes = models.ManyToManyField(
        Event, through='EventWish', related_name='applicants', blank=True)

    # Wishes she is accepted to
    assignation_event = models.ManyToManyField(
        Event, related_name='assigned_applicants', blank=True)

    # Review of the application
    labels = models.ManyToManyField(ApplicantLabel, blank=True)

    def __str__(self):
        return str(self.user) + '@' + str(self.edition)

    def list_of_assignation_wishes(self):
        return [event for event in self.assignation_wishes.all()]

    def list_of_assignation_event(self):
        return [event for event in self.assignation_event.all()]

    @staticmethod
    def for_user_and_edition(user, edition):
        """
        Get applicant object corresponding to an user for given edition. If no
        applicant has been created for this edition yet, it will be created.
        """
        applicant, created = Applicant.objects.get_or_create(
            user=user, edition=edition)

        if created:
            applicant.save()

        return applicant

    class AlreadyLocked(Exception):
        """
        This exception is raised if a new application is submitted for an user
        who has already been accepted or rejected this year.
        """

    class Meta:
        unique_together = (('user', 'edition'), )


class EventWish(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    # Priority defined by the candidate to express his preferred event
    # The lower the order is, the more important is the choice
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ('order', )
        unique_together = (('applicant', 'event'), )

    def __str__(self):
        return '{} for {}'.format(
            str(self.applicant),
            str(self.event)
        )


@ChoiceEnum.labels(str.capitalize)
class AnswerTypes(ChoiceEnum):
    boolean = 0
    integer = 1
    date = 2
    string = 3
    text = 4
    multichoice = 5


class Form(models.Model):
    # Name of the form
    name = models.CharField(max_length=64)
    # List of question
    question_list = models.ManyToManyField('Question')

    def __str__(self):
        return self.name


class Question(models.Model):
    """
    A generic question type, that can be of several type.

    If response_type is multichoice you have to specify the answer in the meta
    field, respecting the following structure:
    {
        "choices": {
            "0": "first option",
            "1": "second option"
        }
    }
    """
    # Formulation of the question
    question = models.TextField()
    # Potential additional indications about the questions
    comment = models.TextField(blank=True)
    # How to represent the answer
    response_type = EnumField(AnswerTypes)
    # Wether the answer is mandatory or not
    required = models.BooleanField(default=False)
    # Some extra constraints on the answer
    meta = JSONField(encoder=DjangoJSONEncoder, default=dict, null=True)

    def __str__(self):
        return self.question


class Answer(models.Model):
    applicant = models.ForeignKey(Applicant, related_name='answers',
                                  on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = JSONField(encoder=DjangoJSONEncoder)

    def __str__(self):
        if self.question.response_type == AnswerTypes.multichoice.value:
            if str(self.response) not in self.question.meta['choices']:
                return ''

            return self.question.meta['choices'][str(self.response)]

        return str(self.response)

    class Meta:
        unique_together = (('applicant', 'question'), )


class SubscriberEmail(models.Model):
    email = models.EmailField()
    date = models.DateTimeField(auto_now_add=True)

    @property
    def unsubscribe_token(self):
        subscriber_id = str(self.id).encode()
        secret = settings.SECRET_KEY.encode()
        return hashlib.sha256(subscriber_id + secret).hexdigest()[:32]

    @property
    def unsubscribe_url(self):
        return reverse('gcc:news_unsubscribe', kwargs={
            'email': self.email, 'token': self.unsubscribe_token})

    def __str__(self):
        return self.email
