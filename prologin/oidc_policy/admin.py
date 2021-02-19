from django.contrib import admin
from .models import OpenIDClientPolicy

class OpenIDClientPolicyAdmin(admin.ModelAdmin):
    search_fields = ('openid_client__name',)
    list_display = (
        'openid_client',
        'allow_staff',
        'allow_assigned_semifinal',
        'allow_assigned_semifinal_event',
        'allow_assigned_final',
    )
    list_filter = (
        'allow_staff',
        'allow_assigned_final',
        'allow_assigned_semifinal',
        'allow_groups',
    )

admin.site.register(OpenIDClientPolicy, OpenIDClientPolicyAdmin)
