from django.views.generic import ListView

import centers.models


class CenterListView(ListView):
    template_name = 'centers/map.html'
    model = centers.models.Center
    context_object_name = 'centers'

    def get_queryset(self):
        return super().get_queryset().active_for_prologin().filter(
            type=centers.models.Center.Type.center.value)
