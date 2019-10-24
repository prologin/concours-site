from django.contrib import admin
import conflose


class ConfloseAdmin(admin.ModelAdmin):
    list_display = ['name']


class UserConfloseAdmin(admin.ModelAdmin):
    autocomplete_fields = ['user']
    list_display = ['user', 'conflose']


admin.site.register(conflose.models.Conflose, ConfloseAdmin)
admin.site.register(conflose.models.UserConflose, UserConfloseAdmin)
