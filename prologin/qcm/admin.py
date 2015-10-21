from django import forms
from django.contrib import admin
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from adminsortable.admin import SortableAdmin, NonSortableParentAdmin, SortableTabularInline

from prologin.utils import admin_url_for

import qcm.models


class AnswerAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = self.fields['proposition'].queryset
        self.fields['proposition'].queryset = qs.filter(question=self.instance.proposition.question)


class QuestionsInline(SortableTabularInline):
    # TODO: cache for_sponsor queryset
    model = qcm.models.Question
    extra = 1


class PropositionsInline(admin.TabularInline):
    model = qcm.models.Proposition
    readonly_fields = ('question',)
    extra = 1


class QcmAdmin(NonSortableParentAdmin):
    list_filter = ('event__edition',)
    list_display = ('event', 'question_count', 'answer_count',)
    search_fields = ('event__edition__year',)
    raw_id_fields = ('event',)
    inlines = [QuestionsInline]

    def question_count(self, obj):
        return obj.question_count
    question_count.short_description = _("Questions")

    def answer_count(self, obj):
        return obj.answer_count
    answer_count.short_description = _("Answers")


class QuestionAdmin(SortableAdmin):
    list_filter = ('qcm__event__edition',)
    list_display = ('body', 'qcm_event_edition', 'proposition_count', 'correct_proposition_count',)
    search_fields = ('qcm__event__edition__year', 'body', 'verbose', 'for_sponsor__name',)
    allow_tags = ('body', 'verbose',)
    inlines = [PropositionsInline]

    def qcm_event_edition(self, obj):
        return admin_url_for(obj.qcm.event.edition)
    qcm_event_edition.allow_tags = True
    qcm_event_edition.short_description = _("Edition")

    def proposition_count(self, obj):
        return obj.proposition_count
    proposition_count.short_description = _("Propositions")

    def correct_proposition_count(self, obj):
        return obj.correct_proposition_count
    correct_proposition_count.short_description = _("Correct propositions")


class AnswerAdmin(admin.ModelAdmin):
    list_filter = ('proposition__question__qcm__event__edition', 'proposition__is_correct',)
    list_display = ('answer_display', 'proposition_question_qcm_event_edition', 'contestant_user', 'proposition_text',
                    'is_correct', 'proposition_question',)
    search_fields = ('contestant__user__username', 'contestant__user__first_name', 'contestant__user__last_name',
                     'proposition__text', 'proposition__question__body', 'proposition__question__verbose',
                     'proposition__question__qcm__event__edition__year')
    raw_id_fields = ('contestant',)
    allow_tags = ('proposition',)
    form = AnswerAdminForm

    def answer_display(self, obj):
        if obj.proposition.question.is_open_ended:
            return _("Answer %(id)s: %(answer)s") % {'id': obj.pk,
                                                     'answer': obj.textual_answer}
        else:
            return _("Answer %(id)s") % {'id': obj.pk}

    def proposition_question_qcm_event_edition(self, obj):
        return admin_url_for(obj.proposition.question.qcm.event.edition)
    proposition_question_qcm_event_edition.allow_tags = True
    proposition_question_qcm_event_edition.admin_order_field = 'proposition__question__qcm__event__edition'
    proposition_question_qcm_event_edition.short_description = _("Edition")

    def proposition_question(self, obj):
        # So we can have HTML questions
        return admin_url_for(obj.proposition.question, label=lambda u: mark_safe(strip_tags(u.body)))
    proposition_question.allow_tags = True
    proposition_question.short_description = _("Question")
    proposition_question.admin_order_field = 'proposition__question__body'

    def proposition_text(self, obj):
        # So we can have HTML propositions
        return mark_safe(strip_tags(obj.proposition.text))
    proposition_text.allow_tags = True
    proposition_text.admin_order_field = 'proposition__text'

    def contestant_user(self, obj):
        return admin_url_for(obj.contestant.user)
    contestant_user.allow_tags = True
    contestant_user.admin_order_field = 'contestant__user__username'
    contestant_user.short_description = _("Contestant")

    def is_correct(self, obj):
        return obj.is_correct
    is_correct.short_description = _("Is correct")
    is_correct.admin_order_field = 'proposition__is_correct'
    is_correct.boolean = True

    def has_add_permission(self, request):
        # We have no admin for Proposition
        return False


admin.site.register(qcm.models.Qcm, QcmAdmin)
admin.site.register(qcm.models.Question, QuestionAdmin)
admin.site.register(qcm.models.Answer, AnswerAdmin)
