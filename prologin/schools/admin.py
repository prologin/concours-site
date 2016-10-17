from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.text import ugettext_lazy as _

import schools.models


class SchoolAdmin(admin.ModelAdmin):
    list_filter = ('approved', 'imported', 'type', 'academy')
    search_fields = ('name', 'acronym', 'uai', 'city')
    list_display = ('name', 'acronym', 'city', 'approved',
                    'total_contestants_count',
                    'current_edition_contestants_count')
    actions = ['merge']

    def merge(self, request, queryset):
        pks = ','.join(map(str, queryset.values_list('pk', flat=True)))
        return HttpResponseRedirect(reverse('schools:admin:merge', args=[pks]))

    merge.short_description = _("Merge selected schools…")


admin.site.register(schools.models.School, SchoolAdmin)
