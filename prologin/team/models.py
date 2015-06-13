from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _


class Role(models.Model):
    rank = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=32)

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")

    @property
    def member_count(self):
        return self.members.count()

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='team_memberships')
    role = models.ForeignKey(Role, related_name='members')
    year = models.PositiveIntegerField(db_index=True)

    class Meta:
        verbose_name = _("Team member")
        verbose_name_plural = _("Team members")
        ordering = ['role__rank', 'user__username']

    def __str__(self):
        return self.user.username
