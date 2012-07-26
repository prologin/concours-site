from contest.models import Contest, Contestant, Score
from django.contrib import admin

class ContestAdmin(admin.ModelAdmin):
	list_display = ('year',)

class ContestantAdmin(admin.ModelAdmin):
	list_display = ('user',)

class ScoreAdmin(admin.ModelAdmin):
	list_display = ('contestant', 'type', 'score')

admin.site.register(Contest, ContestAdmin)
admin.site.register(Contestant, ContestantAdmin)
admin.site.register(Score, ScoreAdmin)
