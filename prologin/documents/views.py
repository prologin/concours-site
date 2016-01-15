import collections
import itertools

from django.conf import settings
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.views.generic import TemplateView

import contest.models
from documents.base_views import BaseContestDocumentView, BaseContestCompilationView

USER_LIST_ORDERING = ('user__last_name', 'user__first_name')


class IndexView(TemplateView):
    template_name = 'documents/index.html'

    def get_context_data(self, **kwargs):
        years = contest.models.Edition.objects.values_list('year', flat=True)
        year = None
        semifinals = None
        final = None
        try:
            year = int(self.kwargs['year'])
            semifinals = contest.models.Event.semifinals_for_edition(year)
            try:
                final = contest.models.Event.final_for_edition(year)
            except contest.models.Event.DoesNotExist:
                final = None
        except (KeyError, ValueError, TypeError):
            pass
        return {**super().get_context_data(**kwargs),
                'years': years,
                'year': year,
                'semifinals': semifinals,
                'final': final}


class SemifinalsConvocationsView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.semifinal
    template_name = 'documents/convocation-regionale.tex'
    pdf_title = _("Prologin %(year)s: batch invitations to the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "invitations-%(year)s-regional-%(center)s")

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'contestants': self.contestants.order_by('edition__year', *USER_LIST_ORDERING),
                'url': settings.SITE_BASE_URL}


class SemifinalsContestantConvocationView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.semifinal
    template_name = 'documents/convocation-regionale.tex'
    pdf_title = _("Prologin %(year)s: invitation to the regional event for %(fullname)s")
    filename = pgettext_lazy("Document filename", "invitation-%(year)s-regional-%(fullname)s")

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'contestants': [self.contestant],
                'url': settings.SITE_BASE_URL}


class SemifinalsContestantsView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.semifinal
    template_name = 'documents/liste-appel.tex'
    pdf_title = _("Prologin %(year)s: call list for the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "call-list-%(year)s-regional-%(center)s")

    def get_context_data(self, **kwargs):
        contestants = itertools.groupby(self.contestants.order_by('assignation_semifinal_event__center__name',
                                                                  *USER_LIST_ORDERING),
                                        lambda w: w.assignation_semifinal_event.center)
        contestants = [(center, list(group)) for center, group in contestants]
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'center_contestants': contestants}


class SemifinalsPortrayalAgreementView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.semifinal
    template_name = 'documents/droit-image-regionale.tex'
    pdf_title = _("Prologin %(year)s: batch portrayal agreements for the regional events")
    filename = pgettext_lazy("Document filename", "portrayal-agreements-%(year)s-regional")

    def get_context_data(self, **kwargs):
        locations = collections.defaultdict(list)
        for event in self.events:
            locations[event.date_begin.date()].append(event.center.city)
        locations = [(date, ', '.join(cities).title()) for date, cities in locations.items()]
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'locations': locations}


class SemifinalsPasswordsView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.semifinal
    template_name = 'documents/passwords.tex'
    pdf_title = _("Prologin %(year)s: password sheets for the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "password-list-%(year)s-regional-%(center)s")

    def get_context_data(self, **kwargs):
        contestants = itertools.groupby(self.contestants.order_by('assignation_semifinal_event__center__name',
                                                                  *USER_LIST_ORDERING),
                                        lambda w: w.assignation_semifinal_event.center)
        contestants = [(center, list(group)) for center, group in contestants]
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'center_contestants': contestants}


class SemifinalsInterviewsView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.semifinal
    template_name = 'documents/interviews.tex'
    pdf_title = _("Prologin %(year)s: interview sheets for the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "interviews-%(year)s-regional-%(center)s")

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'contestants': self.contestants.order_by('assignation_semifinal_event__center__name',
                                                         *USER_LIST_ORDERING)}


class SemifinalsContestantCompilationView(BaseContestCompilationView):
    compiled_classes = (SemifinalsContestantConvocationView, SemifinalsPortrayalAgreementView)
    event_type = contest.models.Event.Type.semifinal
    pdf_title = _("Prologin %(year)s: document compilation for regional events for %(fullname)s")
    filename = pgettext_lazy("Document filename", "prologin-%(year)s-regional-documents-%(fullname)s")


class FinalConvocationsView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.final
    template_name = 'documents/convocation-finale.tex'
    pdf_title = _("Prologin %(year)s: batch invitations to the final")
    filename = pgettext_lazy("Document filename", "invitations-%(year)s-final")

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'event': self.final_event,
                'contestants': self.contestants.order_by(*USER_LIST_ORDERING)}


class FinalContestantConvocationView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.final
    template_name = 'documents/convocation-finale.tex'
    pdf_title = _("Prologin %(year)s: invitation to the final for %(fullname)s")
    filename = pgettext_lazy("Document filename", "invitation-%(year)s-final-%(fullname)s")

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'event': self.final_event,
                'contestants': [self.contestant],
                'url': settings.SITE_BASE_URL}


class FinalContestantsView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.final
    template_name = 'documents/liste-appel.tex'
    pdf_title = _("Prologin %(year)s: call list for the final")
    filename = pgettext_lazy("Document filename", "call-list-%(year)s-final")

    def get_context_data(self, **kwargs):
        contestants = [(self.final_event.center, self.contestants.order_by(*USER_LIST_ORDERING))]
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'center_contestants': contestants}


class FinalPortrayalAgreementView(BaseContestDocumentView):
    template_name = 'documents/droit-image-finale.tex'
    event_type = contest.models.Event.Type.final
    pdf_title = _("Prologin %(year)s: batch portrayal agreements for the final")
    filename = pgettext_lazy("Document filename", "portrayal-agreements-%(year)s-final")

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'events': self.events}


class FinalsPasswordsView(BaseContestDocumentView):
    event_type = contest.models.Event.Type.final
    template_name = 'documents/passwords.tex'
    pdf_title = _("Prologin %(year)s: password sheets for the final")
    filename = pgettext_lazy("Document filename", "password-list-%(year)s-final")

    def get_context_data(self, **kwargs):
        contestants = [(self.final_event.center, self.contestants.order_by(*USER_LIST_ORDERING))]
        return {**super().get_context_data(**kwargs),
                'year': self.year,
                'center_contestants': contestants}


class FinalContestantCompilationView(BaseContestCompilationView):
    compiled_classes = (FinalContestantConvocationView, FinalPortrayalAgreementView)
    event_type = contest.models.Event.Type.final
    pdf_title = _("Prologin %(year)s: document compilation for final for %(fullname)s")
    filename = pgettext_lazy("Document filename", "prologin-%(year)s-final-documents-%(fullname)s")
