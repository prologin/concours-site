from team.models import Team, Role
from django.contrib import admin

class TeamAdmin(admin.ModelAdmin):
    list_display = ('year', 'profile', 'role')

class RoleAdmin(admin.ModelAdmin):
    list_display = ('role', 'rank')

admin.site.register(Team, TeamAdmin)
admin.site.register(Role, RoleAdmin)
