# coding=utf-8
from contest.models import Contest, Contestant, Event, Score
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect

class ContestAdmin(admin.ModelAdmin):
    list_display = ('year',)

class ContestantAdmin(admin.ModelAdmin):
    list_display = ('user',)

class EventAdmin(admin.ModelAdmin):
    list_display = ('contest', 'center', 'type', 'begin', 'end')
    actions = ['export_selected_objects']
    def export_selected_objects(modeladmin, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ct = ContentType.objects.get_for_model(queryset.model)
        return HttpResponseRedirect('/export/?ct={0}&ids={1}'.format(ct.pk, ','.join(selected)))
    export_selected_objects.short_description = u'Générer les convocations'

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('contestant', 'type', 'score')

admin.site.register(Contest, ContestAdmin)
admin.site.register(Contestant, ContestantAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Score, ScoreAdmin)
