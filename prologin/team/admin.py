from django.contrib import admin
from team.models import TeamMember, Role


class TeamMemberAdmin(admin.ModelAdmin):
    list_filter = ('year', 'role',)
    list_display = ('user', 'year', 'role',)
    raw_id_fields = ('user',)


class RoleAdmin(admin.ModelAdmin):
    ordering = ('-significance',)
    list_display = ('name', 'significance', 'member_count',)


admin.site.register(TeamMember, TeamMemberAdmin)
admin.site.register(Role, RoleAdmin)
