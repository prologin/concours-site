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
        current_edition = Edition.objects.latest('year')
        context['edition'] = current_edition
        context['applicants'] = Applicant.objects.filter(edition=current_edition)
        context['labels'] = ApplicantLabel.objects.all()
        return context


class ApplicationRemoveLabelView(CanReviewApplicationPermissionMixin, View):
    def get(self, request, *args, **kwargs):
        applicant = get_object_or_404(Applicant, pk=kwargs['applicant_id'])
        label = get_object_or_404(ApplicantLabel, pk=kwargs['label_id'])
        applicant.labels.remove(label)
        return redirect(
            reverse_lazy('gcc:application_review') + '#applicant-{}'.format(applicant.pk))


class ApplicationAddLabelView(CanReviewApplicationPermissionMixin, View):
    def get(self, request, *args, **kwargs):
        applicant = get_object_or_404(Applicant, pk=kwargs['applicant_id'])
        label = get_object_or_404(ApplicantLabel, pk=kwargs['label_id'])
        applicant.labels.add(label)
        return redirect(
            reverse_lazy('gcc:application_review') + '#applicant-{}'.format(applicant.pk))
