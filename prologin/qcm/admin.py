from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from ordered_model.admin import OrderedModelAdmin

from prologin.utils import admin_url_for

import qcm.models


class QuestionsInline(admin.TabularInline):
    # TODO: cache for_sponsor queryset
    model = qcm.models.Question
    extra = 1


class PropositionsInline(admin.TabularInline):
    model = qcm.models.Proposition
    readonly_fields = ('question',)
    extra = 1


class QcmAdmin(admin.ModelAdmin):
    list_filter = ('event__edition',)
    list_display = ('event', 'question_count', 'answer_count',)
    search_fields = ('event__edition__year',)
    readonly_fields = ('event',)
    inlines = [QuestionsInline]

    def question_count(self, obj):
        return obj.question_count
    question_count.short_description = _("Questions")

    def answer_count(self, obj):
        return obj.answer_count
    answer_count.short_description = _("Answers")


class QuestionAdmin(OrderedModelAdmin):
    list_filter = ('qcm__event__edition',)
    list_display = ('body', 'qcm_event_edition', 'proposition_count', 'correct_proposition_count',)
    search_fields = ('qcm__event__edition__year', 'body', 'verbose', 'for_sponsor__name',)
    # FIXME: if qcm is readonly, it uses question.qcm.__str__, which bypasses .objects,
    # thus there is no question_count, thus is crashes
    # readonly_fields = ('qcm',)
    allow_tags = ('body', 'verbose',)
    inlines = [PropositionsInline]

    def qcm_event_edition(self, obj):
        return obj.qcm.event.edition
    qcm_event_edition.short_description = _("Edition")

    def proposition_count(self, obj):
        return obj.proposition_count
    proposition_count.short_description = _("Propositions")

    def correct_proposition_count(self, obj):
        return obj.correct_proposition_count
    correct_proposition_count.short_description = _("Correct propositions")


class AnswerAdmin(admin.ModelAdmin):
    list_filter = ('proposition__question__qcm__event__edition', 'proposition__is_correct',)
    list_display = ('proposition_question_qcm_event_edition', 'contestant_user', 'proposition_question', 'proposition',
                    'is_correct',)
    search_fields = ('contestant__user__username', 'contestant__user__first_name', 'contestant__user__last_name',
                     'proposition__text', 'proposition__question__body', 'proposition__question__verbose',
                     'proposition__question__qcm__event__edition__year')
    readonly_fields = ('proposition', 'contestant',)
    allow_tags = ('proposition',)

    def proposition_question_qcm_event_edition(self, obj):
        return obj.proposition.question.qcm.event.edition
    proposition_question_qcm_event_edition.admin_order_field = 'proposition__question__qcm__event__edition'
    proposition_question_qcm_event_edition.short_description = _("Edition")

    def proposition_question(self, obj):
        return admin_url_for(obj.proposition.question, label=lambda u: u.body)
        # return obj.proposition.question#
    proposition_question.allow_tags = True
    proposition_question.admin_order_field = 'proposition__question__body'

    def contestant_user(self, obj):
        return obj.contestant.user
    contestant_user.admin_order_field = 'contestant__user__username'
    contestant_user.short_description = _("Contestant")

    def is_correct(self, obj):
        return obj.is_correct
    is_correct.admin_order_field = 'proposition__is_correct'
    is_correct.boolean = True


admin.site.register(qcm.models.Qcm, QcmAdmin)
admin.site.register(qcm.models.Question, QuestionAdmin)
admin.site.register(qcm.models.Answer, AnswerAdmin)