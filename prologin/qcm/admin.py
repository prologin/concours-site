from django.contrib import admin
import qcm.models


class QuestionsInline(admin.TabularInline):
    model = qcm.models.Question
    extra = 1


class PropositionsInline(admin.TabularInline):
    model = qcm.models.Proposition
    extra = 1


class QcmAdmin(admin.ModelAdmin):
    inlines = [QuestionsInline]


class QuestionAdmin(admin.ModelAdmin):
    list_filter = ('qcm',)
    list_display = ('body', 'qcm', 'proposition_count', 'correct_proposition_count',)
    inlines = [PropositionsInline]


admin.site.register(qcm.models.Qcm, QcmAdmin)
admin.site.register(qcm.models.Question, QuestionAdmin)