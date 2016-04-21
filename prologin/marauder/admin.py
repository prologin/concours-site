from django.contrib import admin
from django.utils.translation import ugettext as _

import marauder.models


class UserProfileAdmin(admin.ModelAdmin):
    list_filter = ('in_area', )
    list_display = ('user', 'in_area', 'lat', 'lon')
    search_fields = ('user', 'in_area')
    raw_id_fields = ('user', )


admin.site.register(marauder.models.UserProfile, UserProfileAdmin)


class TaskForceAdmin(admin.ModelAdmin):
    list_filter = ('event', 'name')
    list_display = ('name', 'event', 'members_count')
    search_fields = ('event', 'name')
    raw_id_fields = ('event', 'members', )


admin.site.register(marauder.models.TaskForce, TaskForceAdmin)


class EventSettingsAdmin(admin.ModelAdmin):
    list_filter = ('event', )
    list_display = ('event', 'is_current', 'lat', 'lon', 'radius_meters',
                    'enable_on')
    search_fields = ('event', 'is_current')


admin.site.register(marauder.models.EventSettings, EventSettingsAdmin)
