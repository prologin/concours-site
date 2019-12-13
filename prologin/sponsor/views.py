import random
from django.views.generic import TemplateView

from sponsor.models import Sponsor

class IndexView(TemplateView):
    template_name = 'sponsor/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sponsors = list(Sponsor.active.all())

        random.shuffle(sponsors)
        sponsors.sort(key=lambda sponsor: sponsor.rank_significance, reverse=True)

        context['sponsors'] = sponsors
        return context
