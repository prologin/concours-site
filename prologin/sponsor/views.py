import random
from django.views.generic import TemplateView
from django.utils import translation

from sponsor.models import Sponsor

class IndexView(TemplateView):
    template_name = 'sponsor/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sponsors = list(Sponsor.active.all())

        random.shuffle(sponsors)

        context['sponsors_gold'] = [x for x in sponsors if x.rank == "gold"]
        context['sponsors_silver'] = [x for x in sponsors if x.rank == "silver"]
        context['sponsors_bronze'] = [x for x in sponsors if x.rank == "bronze"]

        return context
