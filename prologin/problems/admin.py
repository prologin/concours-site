from django.contrib import admin
from django.db.models import F, Count
from django.utils.translation import ugettext_lazy as _
import problems.models
from prologin.utils import admin_url_for


class SucceededFilter(admin.SimpleListFilter):
    title = _("succeeded")
    parameter_name = 'succeeded'

    def lookups(self, request, model_admin):
        return (('1', _("Yes")),
                ('0', _("No")))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(score_base__gt=0)
        elif self.value() == '0':
            return queryset.filter(score_base=0)
        return queryset


class CodeStatusFilter(admin.SimpleListFilter):
    title = _("status")
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (('pending', _("Pending")),
                ('failed', _("Failed")),
                ('corrected', _("Corrected")))

    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(score__isnull=True)
        elif self.value() == 'failed':
            return queryset.filter(score=0)
        elif self.value() == 'corrected':
            return queryset.filter(score__gt=0)
        return queryset


class SubmissionCodeAdmin(admin.ModelAdmin):
    readonly_fields = ('submission',)
    list_display = ('_title', 'challenge', 'problem', 'username', 'language', 'score', 'status')
    list_filter = (CodeStatusFilter, 'language', 'submission__challenge')

    def has_add_permission(self, request):
        # Add permission makes no sense as user is read-only
        return False

    def _title(self, obj):
        return _("Code %(id)s") % {'id': obj.pk}
    _title.short_description = _("Code submission")
    _title.admin_order_field = 'pk'

    def challenge(self, obj):
        return obj.submission.challenge
    challenge.short_description = _("Challenge")
    challenge.admin_order_field = 'submission__challenge'

    def problem(self, obj):
        return obj.submission.problem
    problem.short_description = _("Problem")
    problem.admin_order_field = 'submission__problem'

    def username(self, obj):
        return admin_url_for(obj.submission.user, label=lambda u: u.username)
    username.short_description = _("Username")
    username.allow_tags = True
    username.admin_order_field = 'submission__user__username'

    def status(self, obj):
        return obj.status()
    status.short_description = _("Status")
    status.admin_order_field = 'score'

    def get_queryset(self, request):
        # Prevent O(n) queries
        return (super().get_queryset(request)
                .select_related('submission', 'submission__user'))


class SubmissionCodeInline(admin.StackedInline):
    model = problems.models.SubmissionCode
    extra = 0
    readonly_fields = ('date_submitted',)


class SubmissionAdmin(admin.ModelAdmin):
    inlines = [SubmissionCodeInline]
    list_display = ('_title', 'challenge', 'problem', 'username', 'score', 'succeeded')
    list_filter = ('challenge', SucceededFilter)
    readonly_fields = ('user',)

    def has_add_permission(self, request):
        # Add permission makes no sense as user is read-only
        return False

    def _title(self, obj):
        return _("Submission %(id)s") % {'id': obj.pk}
    _title.short_description = _("Submission")
    _title.admin_order_field = 'pk'

    def username(self, obj):
        return admin_url_for(obj.user, label=lambda u: u.username)
    username.short_description = _("Username")
    username.allow_tags = True
    username.admin_order_field = 'user__username'

    def score(self, obj):
        return obj.c_score
    score.short_description = _("Score")
    score.admin_order_field = 'c_score'

    def succeeded(self, obj):
        return obj.c_succeeded
    succeeded.short_description = _("Succeeded")
    succeeded.boolean = True
    succeeded.admin_order_field = 'c_succeeded'

    def get_queryset(self, request):
        # Prevent O(n) queries and add computed score for ordering
        return (super().get_queryset(request)
                .select_related('user')
                .annotate(c_score=F('score_base') - F('malus'))
                .extra(select={'c_succeeded': 'score_base > 0'}))


admin.site.register(problems.models.Submission, SubmissionAdmin)
admin.site.register(problems.models.SubmissionCode, SubmissionCodeAdmin)
