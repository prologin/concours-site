from centers.models import Center
from django.contrib import admin


class CenterAdmin(admin.ModelAdmin):
    list_filter = ('is_active', 'type', 'city')


admin.site.register(Center, CenterAdmin)
