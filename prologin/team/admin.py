from team.models import TeamMember, Role
from django.contrib import admin

class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('year', 'user', 'role')

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rank')

admin.site.register(TeamMember, TeamMemberAdmin)
admin.site.register(Role, RoleAdmin)
