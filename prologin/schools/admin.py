from django.contrib import admin

import schools.models


class SchoolAdmin(admin.ModelAdmin):
    list_filter = ('approved',)
    list_display = ('name', 'approved')


admin.site.register(schools.models.School, SchoolAdmin)
