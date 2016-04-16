from django.views.generic import TemplateView

import prologin.utils


class IndexView(prologin.utils.LoginRequiredMixin, TemplateView):
    template_name = 'marauder/index.html'
