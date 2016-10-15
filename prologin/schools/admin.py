from django.contrib import admin

import schools.models


class SchoolAdmin(admin.ModelAdmin):
    list_filter = ('approved', 'type', 'academy')
    list_display = ('name', 'acronym', 'city', 'approved',
                    'total_contestants_count',
                    'current_edition_contestants_count')


admin.site.register(schools.models.School, SchoolAdmin)
