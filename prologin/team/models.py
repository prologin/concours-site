# coding=utf-8
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Role(models.Model):
    rank = models.IntegerField()
    role = models.CharField(max_length = 32)
    def __unicode__(self):
        return self.role

class Team(models.Model):
    year = models.IntegerField()
    user = models.ForeignKey(User)
    role = models.ForeignKey(Role)

    class Meta:
        verbose_name = 'team'
        verbose_name_plural = 'team'
