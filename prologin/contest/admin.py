from adminsortable.admin import NonSortableParentAdmin, SortableStackedInline
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
import contest.models
from prologin.utils import admin_url_for


class EventWishesFormSet(forms.BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        qs = form.fields['event'].queryset
        form.fields['event'].queryset = qs.filter(type=contest.models.Event.Type.semifinal.value,
                                                  edition=self.instance.edition)
        return form


class ContestantForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = self.fields['assignation_semifinal_event'].queryset
        self.fields['assignation_semifinal_event'].queryset = qs.filter(type=contest.models.Event.Type.semifinal.value,
                                                                        edition=self.instance.edition)


class EventInline(admin.StackedInline):
    # FIXME: center queryset repeated N times
    model = contest.models.Event
    extra = 1


class EventWishesInline(SortableStackedInline):
    # FIXME: event queryset repeated N times
    model = contest.models.EventWish
    extra = 1
    formset = EventWishesFormSet


class CorrectionInline(admin.StackedInline):
    model = contest.models.ContestantCorrection
    extra = 1


class EditionAdmin(admin.ModelAdmin):
    list_filter = ('year',)
    list_display = ('year', 'date_begin', 'date_end',)
    search_fields = ('year',)
    inlines = [EventInline]


class EventAdmin(admin.ModelAdmin):
    list_filter = ('edition', 'center', 'type',)
    list_display = ('type', 'edition_link', 'center_link', 'date_begin', 'date_end',)
    search_fields = ('edition__year', 'center__name',)
    actions = ('export_selected_objects',)

    def export_selected_objects(modeladmin, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ct = ContentType.objects.get_for_model(queryset.model)
        # TODO: use reverse()
        return HttpResponseRedirect('/export/?ct={0}&ids={1}'.format(ct.pk, ','.join(selected)))
    export_selected_objects.short_description = _("Generate convocations")

    def edition_link(self, obj):
        return admin_url_for(obj.edition)
    edition_link.short_description = _("Edition")
    edition_link.admin_order_field = 'edition'
    edition_link.allow_tags = True

    def center_link(self, obj):
        return admin_url_for(obj.center)
    center_link.short_description = _("Center")
    center_link.admin_order_field = 'center'
    center_link.allow_tags = True


class ContestantAdmin(NonSortableParentAdmin):
    list_filter = ('edition',)
    list_display = ('contestant', 'user_link', 'edition_link', 'total_score',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'edition__year',)
    readonly_fields = ('user', 'edition',)
    fieldsets = (
        (None, {'fields': ('user', 'edition',)}),
        (_("Qualification scores"), {'classes': ('collapse',), 'fields':
            ('assignation_semifinal', 'assignation_semifinal_event',
             'score_qualif_qcm', 'score_qualif_algo', 'score_qualif_bonus',)}),
        (_("Regionale scores"), {'classes': ('collapse',), 'fields':
            ('assignation_final', 'score_semifinal_written', 'score_semifinal_interview', 'score_semifinal_machine',
             'score_semifinal_bonus',)}),
        (_("Finale scores"), {'classes': ('collapse',), 'fields':
            ('score_final', 'score_final_bonus',)}),
    )
    inlines = [EventWishesInline, CorrectionInline]
    form = ContestantForm

    def contestant(self, obj):
        return _("%(user)s in edition %(year)s") % {'user': obj.user, 'year': obj.edition.year}

    def user_link(self, obj):
        return admin_url_for(obj.user)
    user_link.short_description = _("User")
    user_link.admin_order_field = 'edition'
    user_link.allow_tags = True

    def edition_link(self, obj):
        return admin_url_for(obj.edition)
    edition_link.short_description = _("Edition")
    edition_link.admin_order_field = 'edition'
    edition_link.allow_tags = True

    def has_add_permission(self, request):
        # Contestants are programmatically created
        return False


admin.site.register(contest.models.Edition, EditionAdmin)
admin.site.register(contest.models.Event, EventAdmin)
admin.site.register(contest.models.Contestant, ContestantAdmin)
