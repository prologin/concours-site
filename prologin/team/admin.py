from django.contrib import admin
from team.models import TeamMember, Role


class TeamMemberAdmin(admin.ModelAdmin):
    list_filter = ('year', 'role')
    list_display = ('year', 'user', 'role')


class RoleAdmin(admin.ModelAdmin):
    list_display = ('rank', 'name')


admin.site.register(TeamMember, TeamMemberAdmin)
admin.site.register(Role, RoleAdmin)
