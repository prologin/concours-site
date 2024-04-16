from django.conf import settings
from django.contrib import admin, messages
from django.utils.translation import ugettext_lazy as _

from django.db.models import QuerySet

import team.models
from team.models import TeamMember


class RoleFilter(admin.SimpleListFilter):
    title = _("Role")
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        return ((role.name, role.value.name_male) for role in team.models.Role)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role_code=self.value())
        return queryset


class TeamMemberAdmin(admin.ModelAdmin):
    list_filter = (RoleFilter, 'year', )
    list_display = ('user', 'year', 'role_significance', 'role_name', )
    raw_id_fields = ('user', )
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    actions = ('copy_to_current_year', )

    def role_significance(self, member):
        return member.role_significance

    role_significance.label = _("Role significance")
    role_significance.admin_order_field = 'role_significance'

    def role_name(self, member):
        return member.role_name_db

    role_name.label = _("Role")
    role_name.admin_order_field = 'role_name_db'

    def copy_to_current_year(self, request, queryset: "QuerySet[TeamMember]"):
        year = settings.PROLOGIN_EDITION
        i = 0
        for member in queryset:
            if TeamMember.objects.filter(user=member.user, year=year).exists():
                continue
            TeamMember.objects.create(user=member.user, role_code=member.role_code, year=year)
            i += 1
        if i > 0:
            self.message_user(request, _("Copied %d team members to year %d") % (i, year))
        else:
            self.message_user(
                request,
                _("Selected team members already exist in year %d") % year,
                level=messages.ERROR,
            )
    copy_to_current_year.short_description = _("Copy selected team members to current year")
    copy_to_current_year.allowed_permissions = ["add"]


admin.site.register(TeamMember, TeamMemberAdmin)
