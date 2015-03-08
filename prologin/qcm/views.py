from django.views.generic import UpdateView
from django.core.urlresolvers import reverse
import qcm.models
import qcm.forms


class DisplayQCMView(UpdateView):
    template_name = "qcm/display.html"
    slug_url_kwarg = 'year'
    pk_url_kwarg = 'year'
    context_object_name = 'qcm'
    form_class = qcm.forms.QcmForm
    model = qcm.models.Qcm

    @property
    def year(self):
        return self.kwargs[self.pk_url_kwarg]

    def get_success_url(self):
        return reverse('qcm:display', args=[self.year])

    def get_object(self, queryset=None):
        return self.model.objects.prefetch_related('questions__propositions').get(event__edition__year=self.year)

    def get_form(self, form_class):
        kwargs = self.get_form_kwargs()
        kwargs['contestant'] = self.request.current_contestant
        return form_class(**kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editable'] = self.request.user.is_authenticated() and self.get_object().event.edition.is_current
        return context
