# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.views.generic import TemplateView

from sponsor.models import Sponsor


class IndexView(TemplateView):
    template_name = 'sponsor/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sponsors'] = Sponsor.active.all()
        return context
