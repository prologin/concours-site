from django.contrib import admin

import schools.models


class SchoolAdmin(admin.ModelAdmin):
    list_filter = ('approved',)
    list_display = ('name', 'approved', 'total_contestants_count',
                    'current_edition_contestants_count')


admin.site.register(schools.models.School, SchoolAdmin)
