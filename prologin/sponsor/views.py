import random
from django.views.generic import TemplateView

from sponsor.models import Sponsor

class IndexView(TemplateView):
    template_name = 'sponsor/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sponsors = list(Sponsor.active.all())
        random.shuffle(sponsors)
        sponsors_super = [x for x in sponsors if x.rank == "super"]
        sponsors_gold = [x for x in sponsors if x.rank == "gold"]
        sponsors_silver = [x for x in sponsors if x.rank == "silver"]
        sponsors_bronze = [x for x in sponsors if x.rank == "bronze"]

        context['sponsors'] = {
            'Gold': sponsors_super + sponsors_gold,
            'Silver': sponsors_silver,
            'Bronze': sponsors_bronze
        }

        return context
