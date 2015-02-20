from django.contrib import admin
from team.models import TeamMember, Role


class TeamMemberAdmin(admin.ModelAdmin):
    list_filter = ('year', 'role',)
    list_display = ('user', 'year', 'role',)


class RoleAdmin(admin.ModelAdmin):
    ordering = ('rank',)
    list_display = ('name', 'rank', 'member_count',)


admin.site.register(TeamMember, TeamMemberAdmin)
admin.site.register(Role, RoleAdmin)
