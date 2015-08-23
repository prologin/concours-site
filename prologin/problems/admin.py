from django.conf import settings
from django.contrib import admin
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import celery
import datetime

from problems.tasks import submit_problem_code
from prologin.utils import admin_url_for
import problems.models


class BooleanFilter(admin.SimpleListFilter):
    q_filter = Q()

    def lookups(self, request, model_admin):
        return (('1', _("Yes")),
                ('0', _("No")))

    def get_queryset(self, request, queryset):
        return queryset

    def get_q_filter(self, request, queryset):
        return self.q_filter

    def queryset_for_true(self, request, queryset):
        return self.get_queryset(request, queryset).filter(self.get_q_filter(request, queryset))

    def queryset_for_false(self, request, queryset):
        return self.get_queryset(request, queryset).exclude(self.get_q_filter(request, queryset))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return self.queryset_for_true(request, queryset)
        elif self.value() == '0':
            return self.queryset_for_false(request, queryset)
        return queryset


class SucceededFilter(BooleanFilter):
    title = _("succeeded")
    parameter_name = 'succeeded'
    q_filter = Q(score_base__gt=0)

    def get_queryset(self, request, queryset):
        return queryset.filter(score_base__isnull=False)


class CodeSucceededFilter(BooleanFilter):
    title = _("succeeded")
    parameter_name = 'succeeded'
    q_filter = Q(score__gt=0)

    def get_queryset(self, request, queryset):
        return queryset.filter(score__isnull=False)


class CodeCorrectedFilter(BooleanFilter):
    title = _("corrected")
    parameter_name = 'corrected'
    q_filter = Q(score__isnull=False)


class CodeExpiredFilter(BooleanFilter):
    title = _("results expired")
    parameter_name = 'expired'

    def get_q_filter(self, request, queryset):
        expiration_date = timezone.now() - datetime.timedelta(seconds=settings.CELERY_TASK_RESULT_EXPIRES)
        return Q(score__isnull=True) & (Q(date_corrected__isnull=True) | Q(date_corrected__lt=expiration_date))


class SubmissionCodeAdmin(admin.ModelAdmin):
    readonly_fields = ('submission',)
    list_display = ('_title', 'challenge', 'problem', 'username', 'language', 'correctable', 'score', 'status')
    list_filter = (CodeSucceededFilter, CodeCorrectedFilter, CodeExpiredFilter, 'language', 'submission__challenge')
    actions = ('submit_to_correction',)

    def has_add_permission(self, request):
        # Add permission makes no sense as user is read-only
        return False

    def _title(self, obj):
        return _("Code %(id)s") % {'id': obj.pk}
    _title.short_description = problems.models.SubmissionCode._meta.verbose_name
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

    def correctable(self, obj):
        return obj.correctable()
    correctable.short_description = _("Correctable")
    correctable.boolean = True
    correctable.admin_order_field = 'language'

    def submit_to_correction(self, request, queryset):
        success = 0
        errors = 0
        for submission in queryset:
            if submission.correctable():
                if not submission.celery_task_id:
                    submission.celery_task_id = celery.uuid()
                    submission.save()
                submit_problem_code.apply_async(args=[submission.pk], task_id=submission.celery_task_id, throw=False)
                success += 1
            else:
                errors += 1
        self.message_user(request, "{success} submissions sent to correction, {errors} uncorrectable skipped".format(
            success=success, errors=errors,
        ))
    submit_to_correction.short_description = _("Submit to correction")

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
    list_filter = (SucceededFilter, 'challenge')
    readonly_fields = ('user',)

    def has_add_permission(self, request):
        # Add permission makes no sense as user is read-only
        return False

    def _title(self, obj):
        return _("Submission %(id)s") % {'id': obj.pk}
    _title.short_description = problems.models.Submission._meta.verbose_name
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
    succeeded.short_description = _("Solved")
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
