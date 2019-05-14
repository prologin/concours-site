from django.views.generic import TemplateView

from sponsor.models import Sponsor


class IndexView(TemplateView):
    template_name = 'sponsor/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sponsors'] = Sponsor.active.all()
        return context
