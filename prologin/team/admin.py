from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

import team.models


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

    def role_significance(self, member):
        return member.role_significance

    role_significance.label = _("Role significance")
    role_significance.admin_order_field = 'role_significance'

    def role_name(self, member):
        return member.role_name_db

    role_name.label = _("Role")
    role_name.admin_order_field = 'role_name_db'


admin.site.register(team.models.TeamMember, TeamMemberAdmin)
