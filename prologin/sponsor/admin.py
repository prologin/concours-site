from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

import sponsor.models


class SponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'site', 'contact_position', 'contact_first_name', 'contact_last_name',
                    'is_active_bool',)
    list_filter = ('is_active',)
    ordering = ('name',)
    search_fields = ('name', 'description', 'comment', 'site',
                     'contact_position', 'contact_email', 'contact_first_name', 'contact_last_name',
                     'contact_phone_desk', 'contact_phone_mobile', 'contact_phone_fax',)

    def is_active_bool(self, obj):
        return obj.is_active
    is_active_bool.admin_order_field = 'is_active'
    is_active_bool.short_description = _("Active")
    is_active_bool.boolean = True


admin.site.register(sponsor.models.Sponsor, SponsorAdmin)
