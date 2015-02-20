import contest.models
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _


class EditionAdmin(admin.ModelAdmin):
    list_filter = ('year',)
    list_display = ('year', 'date_begin', 'date_end',)


class EventWishesInline(admin.StackedInline):
    model = contest.models.EventWish
    extra = 1


class ContestantAdmin(admin.ModelAdmin):
    list_display = ('user', 'edition', 'total_score',)
    fieldsets = (
        (None, {'fields': ('user', 'events',)}),
        (_("Qualification scores"), {'classes': ('collapse',), 'fields':
            ('score_qualif_qcm', 'score_qualif_algo', 'score_qualif_bonus',)}),
        (_("Regionale scores"), {'classes': ('collapse',), 'fields':
            ('score_regionale_written', 'score_regionale_interview', 'score_regionale_machine', 'score_regionale_bonus',)}),
        (_("Finale scores"), {'classes': ('collapse',), 'fields':
            ('score_finale', 'score_finale_bonus',)}),
    )
    inlines = [EventWishesInline]


class EventAdmin(admin.ModelAdmin):
    list_filter = ('edition', 'center', 'type',)
    list_display = ('type', 'edition', 'center', 'date_begin', 'date_end',)
    actions = ['export_selected_objects']

    def export_selected_objects(modeladmin, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ct = ContentType.objects.get_for_model(queryset.model)
        # TODO: use reverse()
        return HttpResponseRedirect('/export/?ct={0}&ids={1}'.format(ct.pk, ','.join(selected)))

    export_selected_objects.short_description = u'Générer les convocations'


admin.site.register(contest.models.Edition, EditionAdmin)
admin.site.register(contest.models.Contestant, ContestantAdmin)
admin.site.register(contest.models.Event, EventAdmin)
