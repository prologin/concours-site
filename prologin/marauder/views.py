from django.utils.functional import cached_property
from django.views.generic.base import ContextMixin, TemplateView
from rules.contrib.views import PermissionRequiredMixin


class MarauderMixin(PermissionRequiredMixin, ContextMixin):
    permission_required = 'marauder.view'

    @cached_property
    def event(self):
        return self.request.current_events['final']

    def get_context_data(self, **kwargs):
        kwargs['event'] = self.event
        return super().get_context_data(**kwargs)


class IndexView(MarauderMixin, TemplateView):
    template_name = 'marauder/index.html'
