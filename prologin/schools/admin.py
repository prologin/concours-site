from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

import contest.models
import schools.models
from prologin.utils.db import AdminOrderFieldsMixin


class SchoolContestantsInline(admin.TabularInline):
    model = contest.models.Contestant
    fields = ['username', 'full_name']
    readonly_fields = fields
    extra = 0

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def username(self, obj):
        return obj.user.username

    def full_name(self, obj):
        return obj.user.get_full_name()

    def get_view_on_site_url(self, obj=None):
        return reverse('users:profile', args=[obj.user.pk])


class SchoolAdmin(AdminOrderFieldsMixin, admin.ModelAdmin):
    def current_edition_count(request):
        return schools.models.School.func_current_edition_contestants_count(request.current_edition.year)

    list_filter = ('approved', 'imported', 'type', 'academy')
    search_fields = ('name', 'acronym', 'uai', 'city')
    list_display = ('name', 'acronym', 'city', 'approved',
                    'tcc', 'cecc')
    annotations = [('tcc', schools.models.School.func_total_contestants_count, _("Total contestant count")),
                   ('cecc', current_edition_count, _("Current edition contestant count"))]
    inlines = [SchoolContestantsInline]
    actions = ['merge']

    def merge(self, request, queryset):
        pks = ','.join(map(str, queryset.values_list('pk', flat=True)))
        return HttpResponseRedirect(reverse('schools:admin:merge', args=[pks]))

    merge.short_description = _("Merge selected schools…")


admin.site.register(schools.models.School, SchoolAdmin)
