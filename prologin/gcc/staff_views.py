from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, View
from rules.contrib.views import PermissionRequiredMixin

from .models import Corrector, Event, Edition, Applicant, ApplicantLabel


class CanEditLabelsPermissionMixin(PermissionRequiredMixin):
    """
    Permission to edit labels for an application.
    This permission is granted if the corrector is allowed to review for an
    event the applicant applies to.
    """

    def has_permission(self):
        return Event.objects.filter(
            correctors__user = self.request.user,
            applicants__id = self.kwargs['applicant_id']
        ).exists()


class CanReviewApplicationPermissionMixin(PermissionRequiredMixin):
    """
    Permission to review for a specific event.
    """

    def has_permission(self):
        return Corrector.objects.filter(
            event__id = self.kwargs['event'],
            user = self.request.user
        ).exists()


class ApplicationReviewView(CanReviewApplicationPermissionMixin, TemplateView):
    template_name = "gcc/application/review.html"

    def get_context_data(self, **kwargs):
        """
        Extract the list of users who have an application this year and list
        their applications in the same object.
        """
        context = super().get_context_data(**kwargs)

        event = Event.objects.get(pk=kwargs['event'])
        applicants = Applicant.objects.filter(assignation_wishes=event)

        assert(event.edition.year == kwargs['edition'])

        return {
            'applicants': applicants,
            'event': event,
            'labels': ApplicantLabel.objects.all()
        }


class ApplicationRemoveLabelView(CanEditLabelsPermissionMixin, View):
    """
    Remove a label attached to an applicant and redirect to specified event's
    review page.
    """

    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs['event_id'])
        applicant = get_object_or_404(Applicant, pk=kwargs['applicant_id'])
        label = get_object_or_404(ApplicantLabel, pk=kwargs['label_id'])

        applicant.labels.remove(label)

        return redirect(
            reverse('gcc:application_review', kwargs = {
                'edition': event.edition.year,
                'event': event.pk
            }) + '#applicant-{}'.format(applicant.pk))


class ApplicationAddLabelView(CanEditLabelsPermissionMixin, View):
    """
    Attach a label to an applicant and redirect to specified event's review
    page.
    """

    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs['event_id'])
        applicant = get_object_or_404(Applicant, pk=kwargs['applicant_id'])
        label = get_object_or_404(ApplicantLabel, pk=kwargs['label_id'])

        applicant.labels.add(label)

        return redirect(
            reverse('gcc:application_review', kwargs = {
                'edition': event.edition.year,
                'event': event.pk
            }) + '#applicant-{}'.format(applicant.pk))

