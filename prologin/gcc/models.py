from django.db import models
from django.conf import settings

from centers.models import Center
from prologin.models import EnumField
from prologin.utils import ChoiceEnum

class Edition(models.Model):
    year = models.PositiveIntegerField(primary_key=True)

class Event(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    event_start = models.DateField(auto_now_add=True)
    event_end = models.DateField(auto_now_add=True)
    signup_start = models.DateField(auto_now_add=True)
    signup_end = models.DateField(auto_now_add=True)

class Trainer(models.Model):
    events = models.ManyToManyField(Event)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    can_view_applications = models.BooleanField(default=False)
    description = models.TextField()

class Application(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    selected = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user','event'),)

class Question(models.Model):
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

    question = models.TextField()
    form = EnumField(Forms)
    response_type = EnumField(ResponseTypes)
    required = models.BooleanField(default=False)
    #TODO: Use postgre's JSONField ?
    meta = models.TextField()

class Response(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    #TODO: Use postgre's JSONField ?
    response = models.TextField()

    class Meta:
        unique_together = (('user','question'),)

class SubscriberEmail(models.Model):
    email = models.EmailField()
