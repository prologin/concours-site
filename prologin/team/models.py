from collections import namedtuple
from django.conf import settings
from django.db import models
from django.db.models import BooleanField, CharField, IntegerField
from django.utils.text import force_text
from django.utils.translation import ugettext_lazy as _, pgettext_lazy

from prologin.models import TextEnumField, Gender
from prologin.utils import ChoiceEnum
from prologin.utils.db import CaseMapping


class RoleData(
        namedtuple('Role', 'name_male name_female title_male title_female significance public')):
    def __lt__(self, other):
        return self.significance.__lt__(other.significance)


class Role(ChoiceEnum):
    president = RoleData(
        pgettext_lazy("male role", "President"),
        pgettext_lazy("female role", "President"),
        pgettext_lazy("male title", "The President"),
        pgettext_lazy("female title", "The President"),
        99, True)
    vice_president = RoleData(
        pgettext_lazy("male role", "Vice President"),
        pgettext_lazy("female role", "Vice President"),
        pgettext_lazy("male title", "The Vice President"),
        pgettext_lazy("female title", "The Vice President"),
        98, True)
    treasurer = RoleData(
        pgettext_lazy("male role", "Treasurer"),
        pgettext_lazy("female role", "Treasurer"),
        None, None, 97, True)
    secretary = RoleData(
        pgettext_lazy("male role", "Secretary"),
        pgettext_lazy("female role", "Secretary"),
        None, None, 96, True)
    technical_lead = RoleData(
        pgettext_lazy("male role", "Technical Lead"),
        pgettext_lazy("female role", "Technical Lead"),
        None, None, 80, True)
    scientific_lead = RoleData(
        pgettext_lazy("male role", "Scientific Lead"),
        pgettext_lazy("female role", "Scientific Lead"),
        None, None, 79, True)
    vice_treasurer = RoleData(
        pgettext_lazy("male role", "Vice Treasurer"),
        pgettext_lazy("female role", "Vice Treasurer"),
        None, None, 70, True)
    member = RoleData(
        pgettext_lazy("male role", "Member"),
        pgettext_lazy("female role", "Member"),
        None, None, 60, True)
    persistent_member = RoleData(
        pgettext_lazy("male role", "Persistent Member"),
        pgettext_lazy("female role", "Persistent Member"),
        None, None, 50, True)
    mascot = RoleData(
        pgettext_lazy("male role", "Mascot"),
        pgettext_lazy("female role", "Mascot"),
        None, None, 40, True)
    external_organizer = RoleData(
        pgettext_lazy("male role", "External organizer"),
        pgettext_lazy("female role", "External organizer"),
        None, None, 0, False)

    @classmethod
    def label_for(cls, member):
        return member.value.name_male

    @classmethod
    def _get_choices(cls):
        return tuple((m.name, cls.label_for(m)) for m in cls)


class TeamMemberManager(models.Manager):
    def get_queryset(self):
        role_significance = CaseMapping('role_code',
                                        ((role.name, role.value.significance)
                                         for role in Role),
                                        output_field=IntegerField())
        role_public = CaseMapping('role_code',
                                  ((role.name, role.value.public)
                                   for role in Role),
                                  output_field=BooleanField())
        role_name_db = CaseMapping(
            'role_code',
            ((role.name, force_text(role.value.name_male)) for role in Role),
            output_field=CharField())
        return (super().get_queryset().select_related('user')
                .annotate(role_significance=role_significance,
                          role_public=role_public,
                          role_name_db=role_name_db)
                .order_by('-role_significance'))


class TeamMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='team_memberships')
    role_code = TextEnumField(Role,
                              verbose_name=_("Role"),
                              db_index=True,
                              blank=False,
                              null=False)
    year = models.PositiveIntegerField(db_index=True)

    objects = TeamMemberManager()

    class Meta:
        ordering = ('user__username', )
        unique_together = ('user', 'year')
        verbose_name = _("Team member")
        verbose_name_plural = _("Team members")

    @property
    def role(self):
        return Role[self.role_code]

    @property
    def role_name(self):
        attr = 'name_female' if self.user.gender == Gender.female.value else 'name_male'
        return getattr(self.role.value, attr)

    @property
    def title_name(self):
        attr = 'title_female' if self.user.gender == Gender.female.value else 'title_male'
        return getattr(self.role.value, attr)

    def __str__(self):
        return self.user.username
