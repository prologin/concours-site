from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import RedirectView, TemplateView
from rules.contrib.views import PermissionRequiredMixin

from gcc.models import Event, Applicant, ApplicantLabel


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

        assert event.edition.year == kwargs['edition']

        return context.update({
            'applicants': applicants,
            'event': event,
            'labels': ApplicantLabel.objects.all()
        })


class ApplicationRemoveLabelView(PermissionRequiredMixin, RedirectView):
    """
    Remove a label attached to an applicant and redirect to specified event's
    review page.
    """
    permission_required = 'gcc.can_edit_application_labels'


    def __init__(self, **kwargs):
        self.event = None
        self.applicant = None
        self.label = None
        super(ApplicationRemoveLabelView, self).__init__(**kwargs)

    def get_permission_object(self):
        return get_object_or_404(Applicant, pk=self.kwargs['applicant'])

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            'gcc:application_review',
            kwargs={
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

    def __init__(self, **kwargs):
        self.event = None
        self.applicant = None
        self.label = None
        super(ApplicationAddLabelView, self).__init__(**kwargs)

    def get_permission_object(self):
        return get_object_or_404(Applicant, pk=self.kwargs['applicant'])

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            'gcc:application_review',
            kwargs={
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
