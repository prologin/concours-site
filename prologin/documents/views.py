import collections
import io
from django.conf import settings
from django.contrib import messages
from django.core import serializers
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.views.generic import TemplateView, View
from django.views.generic.base import RedirectView
from formtools.wizard.views import SessionWizardView
from rules.compat.access_mixins import PermissionRequiredMixin

import contest.models
import documents.forms
import problems.models
from documents.base_views import (BaseSemifinalDocumentView, BaseFinalDocumentView,
                                  BaseCompilationView, USER_LIST_ORDERING)


class IndexRedirect(PermissionRequiredMixin, RedirectView):
    permission_required = 'documents.generate_batch_document'
    permanent = False
    url = reverse_lazy('documents:index', args=[settings.PROLOGIN_EDITION])


class IndexView(PermissionRequiredMixin, TemplateView):
    permission_required = 'documents.generate_batch_document'
    template_name = 'documents/index.html'

    @cached_property
    def year(self):
        return int(self.kwargs['year'])

    def get(self, request, *args, **kwargs):
        self.years = contest.models.Edition.objects.values_list('year', flat=True)
        if self.year not in self.years:
            return HttpResponseRedirect(IndexRedirect.url)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        semifinals = contest.models.Event.semifinals_for_edition(self.year)
        try:
            final = contest.models.Event.final_for_edition(self.year)
        except contest.models.Event.DoesNotExist:
            final = None
        context = super().get_context_data(**kwargs)
        context.update({'years': self.years,
                        'year': self.year,
                        'semifinals': semifinals,
                        'final': final})
        return context


class SemifinalConvocationsView(BaseSemifinalDocumentView):
    template_name = 'documents/convocation-regionale.tex'
    pdf_title = _("Prologin %(year)s: batch invitations to the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "invitations-%(year)s-regional-%(center)s")


class SemifinalContestantConvocationView(BaseSemifinalDocumentView):
    template_name = 'documents/convocation-regionale.tex'
    pdf_title = _("Prologin %(year)s: invitation to the regional event for %(fullname)s")
    filename = pgettext_lazy("Document filename", "invitation-%(year)s-regional-%(fullname)s")


class SemifinalContestantsView(BaseSemifinalDocumentView):
    template_name = 'documents/liste-appel.tex'
    pdf_title = _("Prologin %(year)s: call list for the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "call-list-%(year)s-regional-%(center)s")

    def get_extra_context(self):
        context = super().get_extra_context()
        context['event_contestants'] = self.grouped_event_contestants
        return context


class SemifinalPortrayalAgreementView(BaseSemifinalDocumentView):
    template_name = 'documents/droit-image-regionale.tex'
    pdf_title = _("Prologin %(year)s: portrayal agreement for the regional events")
    filename = pgettext_lazy("Document filename", "portrayal-agreement-%(year)s-regional")

    def get_extra_context(self):
        context = super().get_extra_context()
        locations = collections.defaultdict(list)
        for event in self.events:
            locations[event.date_begin.date()].append(event.center.city)
        locations = [(date, ', '.join(cities).title()) for date, cities in locations.items()]
        locations.sort()
        context['locations'] = locations
        return context


class SemifinalPasswordsView(BaseSemifinalDocumentView):
    template_name = 'documents/passwords.tex'
    pdf_title = _("Prologin %(year)s: password sheets for the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "password-list-%(year)s-regional-%(center)s")

    def get_extra_context(self):
        context = super().get_extra_context()
        context['event_contestants'] = self.grouped_event_contestants
        return context


class SemifinalInterviewsView(BaseSemifinalDocumentView):
    template_name = 'documents/interviews.tex'
    pdf_title = _("Prologin %(year)s: interview sheets for the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "interviews-%(year)s-regional-%(center)s")

    def contestant_queryset(self):
        return super().contestant_queryset().order_by('assignation_semifinal_event__date_begin',
                                                      *USER_LIST_ORDERING)


class SemifinalContestantCompilationView(BaseCompilationView):
    compiled_classes = (SemifinalContestantConvocationView, SemifinalPortrayalAgreementView)
    pdf_title = _("Prologin %(year)s: document compilation for regional events for %(fullname)s")
    filename = pgettext_lazy("Document filename", "prologin-%(year)s-regional-documents-%(fullname)s")

    permission_required = 'documents.generate_semifinal_contestant_document'


class SemifinalDataExportView(PermissionRequiredMixin, View):
    permission_required = 'documents.data_export'

    def get(self, request, *args, **kwargs):
        event = get_object_or_404(contest.models.Event, pk=self.kwargs['event'], edition__year=self.kwargs['year'])

        contestants = (event.assigned_contestants
                       .select_related('user')
                       .filter(user__is_active=True, user__is_staff=False, user__is_superuser=False))

        serializer = serializers.get_serializer('json')()
        stream = io.StringIO()

        def iter_users():
            for contestant in contestants:
                user = contestant.user
                user.set_password(user.plaintext_password)
                user.username = user.normalized_username
                yield user

        def iter_contestants():
            for contestant in contestants:
                yield contestant

        serializer.serialize([event.edition], stream=stream)
        stream.write("\n")
        serializer.serialize([event.center], stream=stream)
        stream.write("\n")
        serializer.serialize([event], stream=stream)
        stream.write("\n")
        serializer.serialize(iter_users(),
                             fields=('username', 'email', 'password', 'first_name', 'last_name', 'phone',
                                     'preferred_locale'),
                             stream=stream)
        stream.write("\n")
        serializer.serialize(iter_contestants(),
                             fields=('edition', 'user', 'preferred_language', 'score_qualif_qcm', 'score_qualif_algo',
                                     'score_qualif_bonus'),
                             stream=stream)
        stream.seek(0)

        response = HttpResponse(stream, content_type='application/json')
        response['Content-Disposition'] = ('attachment; filename="{}.json"'
                                           .format(slugify("export-semifinal-{}-{}"
                                                           .format(event.edition.year, event.center.name))))
        return response


class SemifinalDataImportView(PermissionRequiredMixin, SessionWizardView):
    permission_required = 'documents.data_import'
    file_storage = FileSystemStorage(location=settings.DATA_IMPORT_SEMIFINAL_TEMPORARY_DIR)
    form_list = [('upload', documents.forms.ImportSemifinalResultUploadForm),
                 ('review', documents.forms.ImportSemifinalResultReviewForm)]
    step_names = {'upload': _("Upload result file"),
                  'review': _("Review the imported data")}
    step_templates = {'upload': 'documents/semifinal-import-upload.html',
                      'review': 'documents/semifinal-import-review.html'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['step_name'] = self.step_names[self.steps.current]
        if self.steps.current == 'review':
            context.update(self.get_review_context_data())
        return context

    def get_review_context_data(self):
        result = self.get_cleaned_data_for_step('upload')['file']

        our_contestants = (contest.models.Contestant.objects
                           .filter(assignation_semifinal=contest.models.Assignation.assigned.value,
                                   assignation_semifinal_event=result.event))
        missing_contestant_pk = set(contestant.pk for contestant in our_contestants)

        # Build the contestants list with (imported, contestant, warning list, error list)
        contestants = []
        for imported, contestant in result.contestants:
            warnings = []
            errors = []
            missing_contestant_pk.discard(imported.pk)
            contestants.append((imported, contestant, warnings, errors))
            if contestant is None:
                errors.append(_("Contestant not found in local database."))
                continue
            if not contestant.is_assigned_for_semifinal or contestant.assignation_semifinal_event != result.event:
                errors.append(_("Contestant not assigned to this regional event."))
            if not contestant.user.is_active:
                warnings.append(_("User is inactive."))

        # Add missing local contestants as errors
        for contestant in our_contestants.filter(pk__in=missing_contestant_pk):
            errors = [_("Contestant not found in imported data.")]
            contestants.append((None, contestant, [], errors))

        # Descendant-sort by number of {errors, warnings}
        contestants.sort(key=lambda attrs: (-len(attrs[3]), -len(attrs[2])))

        return {'contestants': contestants, 'event': result.event}

    def get_template_names(self):
        return [self.step_templates[self.steps.current]]

    def done(self, form_list, **kwargs):
        result = self.get_cleaned_data_for_step('upload')['file']
        event = result.event
        challenge = event.challenge

        valid_user_pk = set()
        submissions = {}

        data = self.get_review_context_data()

        # Extract the list of valid user ids
        for imported, contestant, warnings, errors in data['contestants']:
            if errors or not imported or not contestant:
                continue
            valid_user_pk.add(contestant.user.pk)

        # Create or update submissions (score_base and malus)
        for submission in result.submissions:
            if submission.object.user_id not in valid_user_pk:
                continue
            old_pk = submission.object.pk
            current_submission, created = (problems.models.Submission.objects
                                           .get_or_create(challenge=challenge.name,
                                                          problem=submission.object.problem,
                                                          user=submission.object.user))
            # Overwrite score_base and malus
            current_submission.score_base = submission.object.score_base
            current_submission.malus = submission.object.malus
            current_submission.save()
            # Save reference to old pk for related objects (namely codes)
            submissions[old_pk] = current_submission

        # Create codes, if they do not already exist
        for submissioncode in result.submissioncodes:
            if submissioncode.object.submission_id not in submissions:
                continue
            old_submission_pk = submissioncode.object.submission_id
            current_submission = submissions[old_submission_pk]
            fields = ('code', 'language', 'summary', 'score', 'exec_time', 'exec_memory', 'date_submitted', 'date_corrected')
            current_code, created = (problems.models.SubmissionCode.objects
                                     .get_or_create(submission=current_submission,
                                                    defaults={'celery_task_id': submissioncode.object.celery_task_id},
                                                    **{field: getattr(submissioncode.object, field) for field in fields}))
            if created:
                current_code.save()

        # Create unlocks, if they do not already exist
        for explicitunlock in result.explicitunlocks:
            if explicitunlock.object.user_id not in valid_user_pk:
                continue
            current_unlock, created = (problems.models.ExplicitProblemUnlock.objects
                                       .get_or_create(challenge=explicitunlock.object.challenge,
                                                      problem=explicitunlock.object.problem,
                                                      user=explicitunlock.object.user,
                                                      defaults={'date_created': explicitunlock.object.date_created}))
            if created:
                current_unlock.save()

        messages.success(self.request, _("Successfully imported regional event results."))
        return redirect('contest:correction:semifinal', year=event.edition.year, event=event.pk)


class FinalConvocationsView(BaseFinalDocumentView):
    template_name = 'documents/convocation-finale.tex'
    pdf_title = _("Prologin %(year)s: batch invitations to the final")
    filename = pgettext_lazy("Document filename", "invitations-%(year)s-final")


class FinalContestantConvocationView(BaseFinalDocumentView):
    template_name = 'documents/convocation-finale.tex'
    pdf_title = _("Prologin %(year)s: invitation to the final for %(fullname)s")
    filename = pgettext_lazy("Document filename", "invitation-%(year)s-final-%(fullname)s")


class FinalContestantsView(BaseFinalDocumentView):
    template_name = 'documents/liste-appel.tex'
    pdf_title = _("Prologin %(year)s: call list for the final")
    filename = pgettext_lazy("Document filename", "call-list-%(year)s-final")

    def contestant_queryset(self):
        return super().contestant_queryset().order_by(*USER_LIST_ORDERING)

    def get_extra_context(self):
        context = super().get_extra_context()
        context['event_contestants'] = self.grouped_event_contestants
        return context


class FinalPortrayalAgreementView(BaseFinalDocumentView):
    template_name = 'documents/droit-image-finale.tex'
    pdf_title = _("Prologin %(year)s: portrayal agreement for the final")
    filename = pgettext_lazy("Document filename", "portrayal-agreement-%(year)s-final")


class FinalPasswordsView(BaseFinalDocumentView):
    template_name = 'documents/passwords.tex'
    pdf_title = _("Prologin %(year)s: password sheets for the final")
    filename = pgettext_lazy("Document filename", "password-list-%(year)s-final")

    def get_extra_context(self):
        context = super().get_extra_context()
        context['event_contestants'] = self.grouped_event_contestants
        return context


class FinalParticipationAuthorization(BaseFinalDocumentView):
    template_name = 'documents/autorisation-participation.tex'
    pdf_title = _("Prologin %(year)s: participation authorization for the final")
    filename = pgettext_lazy("Document filename", "participation-authorization-%(year)s-final")


class FinalEquipmentLiabilityRelease(BaseFinalDocumentView):
    template_name = 'documents/decharge-materiel.tex'
    pdf_title = _("Prologin %(year)s: equipment liability release for the final")
    filename = pgettext_lazy("Document filename", "equipment-liability-release-%(year)s-final")


class FinalEmergencyCallList(BaseFinalDocumentView):
    template_name = 'documents/personnes-a-prevenir.tex'
    pdf_title = _("Prologin %(year)s: emergency call list for the final")
    filename = pgettext_lazy("Document filename", "emergency-call-list-%(year)s-final")


class FinalPlanning(BaseFinalDocumentView):
    # TODO: this document is highly dynamic: store in DB? external file include?
    template_name = 'documents/planning.tex'
    pdf_title = _("Prologin %(year)s: planning for the final")
    filename = pgettext_lazy("Document filename", "planning-%(year)s-final")


class FinalContestantCompilationView(BaseCompilationView):
    compiled_classes = (FinalContestantConvocationView, FinalPortrayalAgreementView, FinalParticipationAuthorization,
                        FinalEquipmentLiabilityRelease, FinalEmergencyCallList)  #, FinalPlanning)
    pdf_title = _("Prologin %(year)s: document compilation for final for %(fullname)s")
    filename = pgettext_lazy("Document filename", "prologin-%(year)s-final-documents-%(fullname)s")

    permission_required = 'documents.generate_final_contestant_document'
