from django.conf import settings
from django.db import models
from django.db.models import Count
from django.utils.translation import ugettext as _


class RoleManager(models.Manager):
    def get_queryset(self):
        return (super().get_queryset()
                .annotate(_member_count=Count('members')))


class Role(models.Model):
    significance = models.SmallIntegerField()
    name = models.CharField(max_length=32)

    objects = RoleManager()

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ('-significance',)

    @property
    def member_count(self):
        return self._member_count

    def __str__(self):
        return self.name


class TeamMemberManager(models.Manager):
    def get_queryset(self):
        return (super().get_queryset()
                .select_related('user', 'role'))


class TeamMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='team_memberships')
    role = models.ForeignKey(Role, related_name='members')
    year = models.PositiveIntegerField(db_index=True)

    objects = TeamMemberManager()

    class Meta:
        ordering = ['-role__significance', 'user__username']
        unique_together = ('user', 'year')
        verbose_name = _("Team member")
        verbose_name_plural = _("Team members")

    def __str__(self):
        return self.user.username
