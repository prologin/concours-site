from centers.models import Center
from django.contrib import admin


class CenterAdmin(admin.ModelAdmin):
    list_filter = ('is_active', 'type', 'city',)
    list_display = ('name', 'city', 'type', 'is_active',)


admin.site.register(Center, CenterAdmin)
