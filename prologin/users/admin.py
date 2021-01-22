from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from .models import OpenIDClientPolicy


class ProloginUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (_("Profil"), {'fields': ('gender', 'address', 'postal_code', 'city', 'country', 'phone', 'birthday',
                                  'school_stage',)}),
        (_("Public identity"), {'fields': ('avatar', 'picture', 'signature')}),
        (_("Settings"), {'fields': ('allow_mailing', 'timezone', 'preferred_locale',
                                    'preferred_language',)}),
    )

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

admin.site.register(get_user_model(), ProloginUserAdmin)
admin.site.register(OpenIDClientPolicy, OpenIDClientPolicyAdmin)
