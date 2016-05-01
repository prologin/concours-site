from django.utils.functional import cached_property
from django.views.generic import ListView

import team.models


class IndexView(ListView):
    template_name = 'team/index.html'
    model = team.models.TeamMember
    context_object_name = 'team'

    @cached_property
    def year(self):
        return self.kwargs.get('year', self.request.current_edition.year)

    def get_queryset(self):
        return (super().get_queryset()
                .filter(year=self.year, role_public=True))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['year'] = self.year
        context['timeline'] = team.models.TeamMember.objects.values(
            'year').distinct().order_by('-year')
        return context
