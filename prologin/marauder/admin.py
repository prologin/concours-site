from django.contrib import admin
from django.utils.translation import ugettext as _

import marauder.models


class UserProfileAdmin(admin.ModelAdmin):
    list_filter = ('user', 'in_area')
    list_display = ('user', 'in_area', 'lat', 'lon')
    search_fields = ('user', 'in_area')


admin.site.register(marauder.models.UserProfile, UserProfileAdmin)


class TaskForceAdmin(admin.ModelAdmin):
    list_filter = ('event', 'name')
    list_display = ('name', 'event', 'members_count')
    search_fields = ('event', 'name')


admin.site.register(marauder.models.TaskForce, TaskForceAdmin)
