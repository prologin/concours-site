from django.contrib import admin
from django.utils.translation import ugettext as _

import marauder.models


class TaskForceAdmin(admin.ModelAdmin):
    list_filter = ('event', 'name')
    list_display = ('name', 'event', 'members_count')
    search_fields = ('event', 'name')


admin.site.register(marauder.models.TaskForce, TaskForceAdmin)
