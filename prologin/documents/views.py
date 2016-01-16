import collections
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponseRedirect
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

import contest.models
from documents.base_views import (BaseSemifinalsDocumentView, BaseFinalDocumentView,
                                  BaseCompilationView, USER_LIST_ORDERING)


class IndexRedirect(RedirectView):
    permanent = False
    url = reverse_lazy('documents:index', args=[settings.PROLOGIN_EDITION])


class IndexView(TemplateView):
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


class SemifinalsConvocationsView(BaseSemifinalsDocumentView):
    template_name = 'documents/convocation-regionale.tex'
    pdf_title = _("Prologin %(year)s: batch invitations to the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "invitations-%(year)s-regional-%(center)s")


class SemifinalsContestantConvocationView(BaseSemifinalsDocumentView):
    template_name = 'documents/convocation-regionale.tex'
    pdf_title = _("Prologin %(year)s: invitation to the regional event for %(fullname)s")
    filename = pgettext_lazy("Document filename", "invitation-%(year)s-regional-%(fullname)s")


class SemifinalsContestantsView(BaseSemifinalsDocumentView):
    template_name = 'documents/liste-appel.tex'
    pdf_title = _("Prologin %(year)s: call list for the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "call-list-%(year)s-regional-%(center)s")

    def get_extra_context(self):
        context = super().get_extra_context()
        context['event_contestants'] = self.grouped_event_contestants
        return context


class SemifinalsPortrayalAgreementView(BaseSemifinalsDocumentView):
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


class SemifinalsPasswordsView(BaseSemifinalsDocumentView):
    template_name = 'documents/passwords.tex'
    pdf_title = _("Prologin %(year)s: password sheets for the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "password-list-%(year)s-regional-%(center)s")

    def get_extra_context(self):
        context = super().get_extra_context()
        context['event_contestants'] = self.grouped_event_contestants
        return context


class SemifinalsInterviewsView(BaseSemifinalsDocumentView):
    template_name = 'documents/interviews.tex'
    pdf_title = _("Prologin %(year)s: interview sheets for the regional center %(center)s")
    filename = pgettext_lazy("Document filename", "interviews-%(year)s-regional-%(center)s")

    def contestant_queryset(self):
        return super().contestant_queryset().order_by('assignation_semifinal_event__date_begin',
                                                      *USER_LIST_ORDERING)


class SemifinalsContestantCompilationView(BaseCompilationView):
    compiled_classes = (SemifinalsContestantConvocationView, SemifinalsPortrayalAgreementView)
    pdf_title = _("Prologin %(year)s: document compilation for regional events for %(fullname)s")
    filename = pgettext_lazy("Document filename", "prologin-%(year)s-regional-documents-%(fullname)s")


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


class FinalContestantCompilationView(BaseCompilationView):
    compiled_classes = (FinalContestantConvocationView, FinalPortrayalAgreementView)
    pdf_title = _("Prologin %(year)s: document compilation for final for %(fullname)s")
    filename = pgettext_lazy("Document filename", "prologin-%(year)s-final-documents-%(fullname)s")
