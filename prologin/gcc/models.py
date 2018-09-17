import os

from django.db import models
from django.conf import settings
from django.utils.functional import cached_property

from centers.models import Center
from prologin.models import EnumField
from prologin.utils import ChoiceEnum


class Edition(models.Model):
    year = models.PositiveIntegerField(primary_key=True)

    @cached_property
    def trainers(self):
        """Gets the trainers who participate to this edition"""
        return Trainer.objects.filter(events__edition=self)

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
    event_start = models.DateField(auto_now_add=True)
    event_end = models.DateField(auto_now_add=True)
    signup_start = models.DateField(auto_now_add=True)
    signup_end = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.event_start) + ' ' + str(self.center)


class Trainer(models.Model):
    events = models.ManyToManyField(Event)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    can_view_applications = models.BooleanField(default=False)
    description = models.TextField()

    def __str__(self):
        return str(self.user)


class Application(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    selected = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user', 'event'), )

    def __str__(self):
        if self.accepted:
            status = 'accepted'
        elif self.rejected:
            status = 'rejected'
        else:
            status = 'pending'

        return '{} for {} ({})'.format(
            str(self.user),
            str(self.event),
            status
        )


@ChoiceEnum.labels(str.capitalize)
class Forms(ChoiceEnum):
    application = 0
    profile = 1


@ChoiceEnum.labels(str.capitalize)
class ResponseTypes(ChoiceEnum):
    boolean = 0
    integer = 1
    date = 2
    string = 3
    text = 4


class Question(models.Model):
    question = models.TextField()
    form = EnumField(Forms)
    response_type = EnumField(ResponseTypes)
    required = models.BooleanField(default=False)
    #TODO: Use postgre's JSONField ?
    meta = models.TextField()


class Response(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    #TODO: Use postgre's JSONField ?
    response = models.TextField()

    class Meta:
        unique_together = (('user', 'question'), )


class SubscriberEmail(models.Model):
    email = models.EmailField()

    def __str__(self):
        return self.email
