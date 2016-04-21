from django.utils.functional import cached_property
from django.views.generic.base import ContextMixin, TemplateView

import prologin.utils


class MarauderMixin(ContextMixin):
    @cached_property
    def event(self):
        return self.request.current_events['final']

    def get_context_data(self, **kwargs):
        kwargs['event'] = self.event
        return super().get_context_data(**kwargs)


class IndexView(prologin.utils.LoginRequiredMixin, MarauderMixin,
                TemplateView):
    template_name = 'marauder/index.html'
