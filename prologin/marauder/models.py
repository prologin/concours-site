from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

import contest.models


class TaskForce(models.Model):
    """A task force is a subdivision unit of Prologin's event organizers.

    A given organizer present at an edition's event can be part of 0+ task
    forces. The desired redundancy of a task force can also be configured:
    $redundancy people from the task force should be present onsite at all
    times.
    """
    event = models.ForeignKey(contest.models.Event, related_name='task_forces')
    name = models.CharField(max_length=50)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                     related_name='task_forces')
    redundancy = models.IntegerField(default=0)

    @property
    def members_count(self):
        return self.members.count()

    class Meta:
        verbose_name = _("Task force")
        verbose_name_plural = _("Task forces")
        ordering = ('-event', '-redundancy', 'name')
        unique_together = ('event', 'name')

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Container for per-user data related to Marauder.

    Created automatically when a user starts reporting data to Marauder through
    the reporting API.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='marauder_profile')

    # Location reporting data.
    location_timestamp = models.DateTimeField(auto_now=True)
    in_area = models.BooleanField(default=False)
    lat = models.FloatField(default=0.0)
    lon = models.FloatField(default=0.0)

    # Notification pushing data.
    gcm_app_id = models.CharField(max_length=64)
    gcm_token = models.CharField(max_length=256)

    class Meta:
        verbose_name = _("User profile")
        verbose_name_plural = _("User profiles")
        ordering = ('user', )

    def __str__(self):
        return str(self.user)


class EventSettings(models.Model):
    """Container for per-event settings related to Marauder."""
    event = models.OneToOneField(contest.models.Event,
                                 related_name='marauder_settings')

    # Geofence of the event location. Currently using a circle instead of an
    # arbitrary polygon for simplicity.
    lat = models.FloatField()
    lon = models.FloatField()
    radius_meters = models.FloatField()

    # Provides a way to enable Marauder for a given event before the event
    # officially starts (for testing / preparation purposes).
    enable_on = models.DateTimeField()

    class Meta:
        verbose_name = _("Event settings")
        verbose_name_plural = _("Events settings")
        ordering = ('event', )

    @property
    def is_current(self):
        """Returns whether this event is active for Marauder tracking."""
        now = timezone.now()
        return (now > self.enable_on and now <= self.event.date_end)
