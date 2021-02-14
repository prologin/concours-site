import datetime

from datatableview.views import DatatableView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db import transaction, connection
from django.db.models import Count
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.utils import timezone
from django.utils.functional import cached_property
from django.views.generic import TemplateView, UpdateView, ListView, DetailView
from django.views.generic.edit import ModelFormMixin
from redis import StrictRedis
from rules.contrib.views import PermissionRequiredMixin

import contest.models
import contest.datatables
import contest.staff_forms
import problems.models

User = get_user_model()


class CanCorrectPermissionMixin(PermissionRequiredMixin):
    permission_required = 'correction.can_correct'

    def get_permission_object(self):
        return None


class EditionMixin:
    year_url_kwarg = 'year'

    @cached_property
    def edition(self):
        return (contest.models.Edition.objects
                .prefetch_related('contestants', 'contestants__user')
                .get(year=self.kwargs[self.year_url_kwarg]))

    def get_queryset(self):
        return super().get_queryset().filter(edition=self.edition)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['edition'] = self.edition
        return context


class EventTypeMixin:
    event_type = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_type'] = self.event_type
        return context


class EventMixin:
    event_url_kwarg = 'event'

    @cached_property
    def event(self):
        return get_object_or_404(contest.models.Event, pk=self.kwargs[self.event_url_kwarg], edition=self.edition)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        return context


class IndexView(CanCorrectPermissionMixin, TemplateView):
    template_name = 'correction/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events'] = events = (contest.models.Event.objects
                                      .select_related('edition').order_by('-edition__year', 'type'))
        for event in events:
            if event.type == contest.models.Event.Type.qualification.value:
                event.absolute_url = reverse('contest:correction:qualification',
                                             kwargs={'year': event.edition.year})
            elif event.type == contest.models.Event.Type.semifinal.value:
                event.absolute_url = reverse('contest:correction:semifinal',
                                             kwargs={'year': event.edition.year, 'event': event.pk})
            # we don't care about finals
        context['years'] = sorted(set(event.edition.year for event in events), reverse=True)
        return context


class YearIndexView(CanCorrectPermissionMixin, EditionMixin, ListView):
    template_name = 'correction/by-year.html'
    context_object_name = 'events'
    model = contest.models.Event

    def get_queryset(self):
        qs = (super().get_queryset()
              .select_related('center')
              .exclude(type=contest.models.Event.Type.final.value)
              .order_by('type', 'date_begin', 'center'))
        contestants = (contest.models.Contestant.objects
                       .filter(edition=self.edition)
                       .select_related('assignation_semifinal_event'))
        events_contestants = dict(contest.models.Event.objects
                                  .filter(edition=self.edition, type=contest.models.Event.Type.semifinal.value)
                                  .annotate(c=Count('assigned_contestants'))
                                  .values_list('pk', 'c'))

        try:
            challenge_qualif = problems.models.Challenge.by_year_and_event_type(self.edition.year, contest.models.Event.Type.qualification)
        except ObjectDoesNotExist:
            challenge_qualif = None
        try:
            challenge_semifinal = problems.models.Challenge.by_year_and_event_type(self.edition.year, contest.models.Event.Type.semifinal)
        except ObjectDoesNotExist:
            challenge_semifinal = None

        if challenge_semifinal:
            with connection.cursor() as c:
                c.execute("""
                    SELECT
                      contest_event.id, COUNT(contest_contestant.id)
                    FROM problems_submission
                      INNER JOIN users_prologinuser ON (problems_submission.user_id = users_prologinuser.id)
                      INNER JOIN contest_contestant ON (users_prologinuser.id = contest_contestant.user_id)
                      INNER JOIN contest_event ON (contest_contestant.assignation_semifinal_event_id = contest_event.id)
                    WHERE (contest_event.edition_id = %s AND problems_submission.challenge = %s)
                    GROUP BY contest_event.id
                """, [self.edition.year, challenge_semifinal.name])
                event_submissions = dict(c.fetchall())

        for item in qs:
            if item.type == contest.models.Event.Type.qualification.value:
                item.absolute_url = reverse('contest:correction:qualification', kwargs={'year': self.edition.year})
                item.contestant_count = contestants.count()
                if challenge_qualif:
                    item.submission_count = problems.models.Submission.objects.filter(challenge=challenge_qualif.name).count()
            elif item.type == contest.models.Event.Type.semifinal.value:
                item.absolute_url = reverse('contest:correction:semifinal',
                                            kwargs={'year': self.edition.year, 'event': item.pk})
                item.contestant_count = events_contestants.get(item.pk, 0)
                if challenge_semifinal:
                    item.submission_count = event_submissions.get(item.pk, 0)
            else:
                # what the fuck
                continue
        return qs


class QualificationIndexView(CanCorrectPermissionMixin, EditionMixin, DatatableView):
    template_name = 'correction/qualification.html'
    model = contest.models.Contestant
    context_object_name = 'contestants'
    datatable_class = contest.datatables.ContestantQualificationTable

    def get_queryset(self):
        if self.request.GET.get('incomplete') is not None:
            # the whole queryset, with some related
            return (super().get_queryset()
                    .select_related('user', 'assignation_semifinal_event', 'assignation_semifinal_event__center'))
        # only the complete contestants
        return self.model.complete_for_semifinal.filter(edition=self.edition)


class SemifinalEventIndexView(CanCorrectPermissionMixin, EditionMixin, EventMixin, DatatableView):
    template_name = 'correction/semifinal.html'
    model = contest.models.Contestant
    context_object_name = 'contestants'
    datatable_class = contest.datatables.ContestantSemifinalTable

    def get_queryset(self):
        return (super().get_queryset()
                .select_related('user', 'assignation_semifinal_event',
                                'assignation_semifinal_event__center')
                .filter(assignation_semifinal_event=self.event))


class FinalIndexView(CanCorrectPermissionMixin, EditionMixin, DatatableView):
    template_name = 'correction/final.html'
    model = contest.models.Contestant
    context_object_name = 'contestants'
    datatable_class = contest.datatables.ContestantFinalTable

    def get_queryset(self):
        return (super().get_queryset()
                .select_related('user', 'assignation_semifinal_event',
                                'assignation_semifinal_event__center')
                .filter(assignation_semifinal=contest.models.Assignation
                        .assigned.value))


class SemifinalIndexView(CanCorrectPermissionMixin, EditionMixin, DatatableView):
    template_name = 'correction/semifinal.html'
    model = contest.models.Contestant
    context_object_name = 'contestants'
    datatable_class = contest.datatables.ContestantSemifinalTable

    def get_queryset(self):
        return (super().get_queryset()
                .select_related('user', 'assignation_semifinal_event',
                                'assignation_semifinal_event__center')
                .filter(edition=self.edition))


class ContestantCorrectionView(CanCorrectPermissionMixin, EventTypeMixin, EditionMixin, UpdateView):
    """
    Abstract view for ContestantQualificationView and ContestantSemifinalView.

    Mandatory fields:
      - event_type
      - template_name
      - form_class
      - redirect_url_name
    """
    event_type = None
    form_class = None
    template_name = None
    redirect_url_name = None

    model = contest.models.Contestant
    context_object_name = 'contestant'
    pk_url_kwarg = 'cid'

    def get_success_url(self):
        return reverse('contest:{}'.format(self.redirect_url_name), args=self.args, kwargs=self.kwargs)

    def submissioncode_date_range(self):
        raise NotImplementedError()

    def form_valid(self, form):
        with transaction.atomic():
            old_contestant = self.model.objects.get(pk=self.object.pk)
            self.object = contestant = form.save()
            changes = old_contestant.compute_changes(contestant, self.event_type)
            correction = contest.models.ContestantCorrection(contestant=contestant,
                                                             author=self.request.user,
                                                             event_type=self.event_type.value,
                                                             comment=form.cleaned_data['comment'],
                                                             changes=changes)
            correction.save()
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contestant = context['contestant']

        # The staff corrections
        context['corrections'] = (contestant.corrections
                                  .select_related('contestant', 'author')
                                  .filter(event_type=self.event_type.value)
                                  .order_by('-date_created').distinct())

        # The problem submissions (contestant codes)
        try:
            challenge = problems.models.Challenge.by_year_and_event_type(self.edition.year, self.event_type)
            qs_codes = (problems.models.SubmissionCode.objects
                        .select_related('submission')
                        .filter(submission__challenge=challenge.name,
                                submission__user=contestant.user,
                                date_submitted__range=self.submissioncode_date_range())
                        .order_by('-score', '-date_submitted'))
            name_to_problem = {problem.name: problem for problem in challenge.problems}
            codes = {problem: None for problem in challenge.problems}
            # first pass: put best-score code
            for code in qs_codes:
                problem = name_to_problem[code.submission.problem]
                if codes[problem] is None and code.succeeded():
                    codes[problem] = code
            # second pass: for problems still missing, put the latest failed (or uncorrectable) code
            for code in qs_codes:
                problem = name_to_problem[code.submission.problem]
                if codes[problem] is None:
                    codes[problem] = code

            codes = sorted(codes.items(), key=lambda pair: (pair[0].difficulty, pair[0].title))
        except ObjectDoesNotExist:
            codes = []
        context['submissions'] = codes

        return context


class ContestantQualificationView(ContestantCorrectionView):
    template_name = 'correction/contestant-qualification.html'
    event_type = contest.models.Event.Type.qualification
    form_class = contest.staff_forms.ContestantQualificationForm
    redirect_url_name = 'correction:contestant-qualification'
    
    def submissioncode_date_range(self):
        event = contest.models.Event.objects.get(edition=self.edition, type=self.event_type.value)
        return (event.date_begin, event.date_end)
        
    def get_context_data(self, **kwargs):
        import qcm.forms
        import qcm.models
        context = super().get_context_data(**kwargs)
        contestant = context['contestant']

        # Qualification-specific: quiz (if any)
        try:
            quiz = qcm.models.Qcm.full_objects.get(event__edition=self.edition)
            context['quiz'] = quiz
            context['quiz_form'] = qcm.forms.QcmForm(instance=quiz, contestant=contestant, readonly=True)
        except qcm.models.Qcm.DoesNotExist:
            pass

        return context


class ContestantSemifinalView(EventMixin, ContestantCorrectionView):
    template_name = 'correction/contestant-semifinal.html'
    event_type = contest.models.Event.Type.semifinal
    form_class = contest.staff_forms.ContestantSemifinalForm
    redirect_url_name = 'correction:contestant-semifinal'

    def submissioncode_date_range(self):
        if not self.event:
            raise Http404()
        return (self.event.date_begin, self.event.date_end)

    @cached_property
    def event(self):
        return self.object.assignation_semifinal_event


class ContestantLiveUpdate(CanCorrectPermissionMixin, EditionMixin, DetailView):
    model = contest.models.Contestant
    context_object_name = 'contestant'
    pk_url_kwarg = 'cid'

    @cached_property
    def event_type(self) -> contest.models.Event.Type:
        return contest.models.Event.Type[self.kwargs['type']]

    def get_object(self, queryset=None):
        return ((queryset or self.get_queryset())
                .select_related('assignation_semifinal_event')
                .get(pk=self.kwargs[self.pk_url_kwarg]))

    def get_json_data(self):
        q = {'event_type': self.event_type.value}
        try:
            # filter out old entries
            date_from = int(self.request.GET['from']) + 1  # offset because of timestamp rounding
            q['date_created__gt'] = timezone.make_aware(datetime.datetime.fromtimestamp(date_from), timezone.utc)
        except (ValueError, KeyError):
            pass

        contestant = self.object
        try:
            latest_date = contestant.corrections.filter(event_type=self.event_type.value).latest().date_created_utc
        except contest.models.ContestantCorrection.DoesNotExist:
            latest_date = None
        # we order by date_created *asc* as it will be *prepended* on the frontend
        corrections_qs = contestant.corrections.select_related('author').filter(**q).order_by('date_created').distinct()
        corr_tpl = get_template('correction/chunk-correction.html')
        corrections = [corr_tpl.render({'corr': corr}) for corr in corrections_qs]
        changes = {}
        latest_correction = corrections_qs.last()
        if latest_correction and latest_correction.changes:
            changes = latest_correction.changes

        # presence, through redis
        online_users = [self.request.user]
        online_alive = False
        try:
            self_pk = self.request.user.pk
            timeout = settings.CORRECTION_LIVE_UPDATE_TIMEOUT
            now = timezone.make_naive(timezone.now(), timezone.utc).timestamp()
            moments_ago = now - timeout
            key = settings.CORRECTION_LIVE_UPDATE_REDIS_KEY.format(key=contestant.pk)
            client = StrictRedis(**settings.PROLOGIN_UTILITY_REDIS_STORE)
            client.expire(key, timeout * 2)  # garbage collect the whole set after a bit if no further updates
            client.zadd(key, {self_pk: now})  # add self to the set
            members = client.zrangebyscore(key, moments_ago, '+inf')  # list people that are recent enough
            members = set(int(pk) for pk in members) - {self_pk}  # exclude self
            online_users.extend(User.objects.filter(pk__in=members).order_by('pk'))
            online_alive = True
        except Exception:
            # it's not worth trying harder
            pass

        user_tpl = get_template('correction/chunk-online-user.html')
        online_users = [(user.pk, user_tpl.render({'user': user})) for user in online_users]

        return {
            'changes': changes,
            'corrections': corrections,
            'online': online_users,
            'online_alive': online_alive,
            'from': latest_date,
            'delay': 1000 * settings.CORRECTION_LIVE_UPDATE_POLL_INTERVAL,
        }

    def render_to_response(self, context, **kwargs):
        return JsonResponse(self.get_json_data())
