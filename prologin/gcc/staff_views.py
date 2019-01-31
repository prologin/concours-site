from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, View
from rules.contrib.views import PermissionRequiredMixin

from .models import Corrector, Event, Edition, Applicant, ApplicantLabel


class CanReviewApplicationPermissionMixin(PermissionRequiredMixin):
    def has_permission(self):
        return len(Corrector.objects.filter(event__id=self.kwargs['event'],
                user=self.request.user)) >= 1


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


#TODO: Check some permission, maybe that the person is corrector for at least
#  one of the events?
class ApplicationRemoveLabelView(View):
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


class ApplicationAddLabelView(View):
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

