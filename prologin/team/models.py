from django.conf import settings
from django.db import models


class Role(models.Model):
    rank = models.IntegerField()
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    year = models.IntegerField()
    role = models.ForeignKey(Role)

    class Meta:
        verbose_name = 'team member'
        verbose_name_plural = 'team members'

    def __str__(self):
        return self.user.username
