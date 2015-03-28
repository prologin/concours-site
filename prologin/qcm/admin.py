from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin

import contest.models
import qcm.models


class QuestionsInline(admin.TabularInline):
    model = qcm.models.Question
    extra = 1


class PropositionsInline(admin.TabularInline):
    model = qcm.models.Proposition
    extra = 1


class QcmAdmin(admin.ModelAdmin):
    inlines = [QuestionsInline]
    list_filter = ('event__edition',)
    list_display = ('event', 'questions__count', 'answers__count',)

    def render_change_form(self, request, context, *args, **kwargs):
        qs = context['adminform'].form.fields['event'].queryset
        # Restrict events to qualification only
        context['adminform'].form.fields['event'].queryset = qs.filter(
            type=contest.models.Event.Type.qualification.value)
        return super().render_change_form(request, context, *args, **kwargs)

    def questions__count(self, obj):
        return obj.questions.count()

    def answers__count(self, obj):
        return qcm.models.Answer.objects.filter(proposition__question__qcm=obj).count()


class QuestionAdmin(OrderedModelAdmin):
    list_filter = ('qcm__event__edition',)
    list_display = ('body', 'qcm', 'proposition_count', 'correct_proposition_count',)
    inlines = [PropositionsInline]


class AnswerAdmin(admin.ModelAdmin):
    list_filter = ('proposition__question__qcm__event__edition',)
    list_display = ('proposition__question__qcm', 'contestant', 'proposition__question', 'proposition', 'is_correct',)

    def proposition__question__qcm(self, obj):
        return obj.proposition.question.qcm
    proposition__question__qcm.admin_order_field = 'proposition__question__qcm'

    def proposition__question(self, obj):
        return obj.proposition.question
    proposition__question.admin_order_field = 'proposition__question'


admin.site.register(qcm.models.Qcm, QcmAdmin)
admin.site.register(qcm.models.Question, QuestionAdmin)
admin.site.register(qcm.models.Answer, AnswerAdmin)