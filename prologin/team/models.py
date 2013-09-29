# coding=utf-8
from django.db import models
from users.models import UserProfile

class Role(models.Model):
    rank = models.IntegerField()
    role = models.CharField(max_length = 32)
    def __unicode__(self):
        return self.role

class Team(models.Model):
    year = models.IntegerField()
    profile = models.ForeignKey(UserProfile)
    role = models.ForeignKey(Role)

    class Meta:
        verbose_name = 'team'
        verbose_name_plural = 'team'

    def username(self):
        return self.profile.user.username
