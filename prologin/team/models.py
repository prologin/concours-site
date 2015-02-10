from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _


class Role(models.Model):
    rank = models.IntegerField()
    name = models.CharField(max_length=32)

    class Meta:
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='team_members')
    year = models.IntegerField()
    role = models.ForeignKey(Role, related_name='members')

    class Meta:
        verbose_name = _('Team member')
        verbose_name_plural = _('Team members')

    def __str__(self):
        return self.user.username
