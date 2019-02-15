from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import RedirectView, TemplateView
from rules.contrib.views import PermissionRequiredMixin

from .models import Corrector, Event, Edition, Applicant, ApplicantLabel


class ApplicationReviewView(PermissionRequiredMixin, TemplateView):
    permission_required = 'gcc.can_review_event'
    template_name = "gcc/application/review.html"

    def get_permission_object(self):
        return get_object_or_404(Event, pk=self.kwargs['event'])

    def get_context_data(self, **kwargs):
        """
        Extract the list of users who have an application this year and list
        their applications in the same object.
        """
        context = super().get_context_data(**kwargs)

        event = get_object_or_404(Event, pk=kwargs['event'])
        applicants = Applicant.objects.filter(assignation_wishes=event)

        assert(event.edition.year == kwargs['edition'])

        return {
            'applicants': applicants,
            'event': event,
            'labels': ApplicantLabel.objects.all()
        }


class ApplicationRemoveLabelView(PermissionRequiredMixin, RedirectView):
    """
    Remove a label attached to an applicant and redirect to specified event's
    review page.
    """
    permission_required = 'gcc.can_edit_application_labels'

    def get_permission_object(self):
        return get_object_or_404(Applicant, pk=self.kwargs['applicant'])

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            'gcc:application_review',
            kwargs = {
                'edition': self.applicant.edition.pk,
                'event': self.event.pk
            }
        ) + '#applicant-{}'.format(self.applicant.pk)

    def get(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=kwargs['event'])
        self.applicant = get_object_or_404(Applicant, pk=kwargs['applicant'])
        self.label = get_object_or_404(ApplicantLabel, pk=kwargs['label'])

        if self.has_permission():
            self.applicant.labels.remove(self.label)

        return super().get(request, *args, **kwargs)


class ApplicationAddLabelView(PermissionRequiredMixin, RedirectView):
    """
    Attach a label to an applicant and redirect to specified event's review
    page.
    """
    permission_required = 'gcc.can_edit_application_labels'

    def get_permission_object(self):
        return get_object_or_404(Applicant, pk=self.kwargs['applicant'])

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            'gcc:application_review',
            kwargs = {
                'edition': self.applicant.edition.pk,
                'event': self.event.pk
            }
        ) + '#applicant-{}'.format(self.applicant.pk)

    def get(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=kwargs['event'])
        self.applicant = get_object_or_404(Applicant, pk=kwargs['applicant'])
        self.label = get_object_or_404(ApplicantLabel, pk=kwargs['label'])

        if self.has_permission():
            self.applicant.labels.add(self.label)

        return super().get(request, *args, **kwargs)

