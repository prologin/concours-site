from django.views.generic import ListView, RedirectView

from django.conf import settings
from django.urls import reverse

import centers.models


class CenterListView(ListView):
    template_name = 'centers/map.html'
    model = centers.models.Center
    context_object_name = 'centers'

    def get_queryset(self):
        return super().get_queryset().filter(type=centers.models.Center.Type.center.value,
                                             is_active=True)


class CenterSpecificView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return f'{settings.SITE_BASE_URL}{reverse("centers:map")}#center-{self.kwargs["id"]}'
