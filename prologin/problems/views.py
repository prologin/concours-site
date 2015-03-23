from django.views.generic import UpdateView
from django.conf import settings
from django.db.models import Q
import contest.models
import problems.forms


# FIXME: at the moment this only handles qualification problems
class Index(UpdateView):
    template_name = 'problems/index.html'
    slug_url_kwarg = 'year'
    pk_url_kwarg = 'year'
    context_object_name = 'problems'
    form_class = problems.forms.ProblemsForm
    model = contest.models.Event

    @property
    def year(self):
        return self.kwargs[self.pk_url_kwarg]

    def get_object(self, queryset=None):
        return self.model.objects.get(type=contest.models.Event.Type.qualification.value,
                                      edition__year=self.year)

    def get_form(self, form_class):
        kwargs = self.get_form_kwargs()
        kwargs['contestant'] = self.request.current_contestant
        return form_class(**kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.get_object()
        context['editable'] = self.request.user.is_authenticated()
        return context