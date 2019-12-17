import random
from django.views.generic import TemplateView

from sponsor.models import Sponsor

class IndexView(TemplateView):
    template_name = 'sponsor/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sponsors = list(Sponsor.active.all())

        random.shuffle(sponsors)

        context['sponsors_gold'] = [x for x in sponsors if x.rank_significance == 90]
        context['sponsors_silver'] = [x for x in sponsors if x.rank_significance == 60]
        context['sponsors_bronze'] = [x for x in sponsors if x.rank_significance == 30]
        return context
