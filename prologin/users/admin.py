from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _


class ProloginUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (_("Profil"), {'fields': ('gender', 'address', 'postal_code', 'city', 'country', 'phone', 'birthday',
                                  'school_stage',)}),
        (_("Public identity"), {'fields': ('avatar', 'picture', 'signature')}),
        (_("Settings"), {'fields': ('newsletter', 'allow_mailing', 'timezone', 'preferred_locale',
                                    'preferred_language',)}),
    )

admin.site.register(get_user_model(), ProloginUserAdmin)
