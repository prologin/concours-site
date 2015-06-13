from django.views import generic
from team.models import TeamMember


# from pages.models import Page
#
# class DetailView(generic.DetailView):
#     model = Page
#     template_name = 'pages/detail.html'


class AboutContestView(generic.TemplateView):
    template_name = 'pages/about-contest.html'


class AboutOrganizationView(generic.TemplateView):
    template_name = 'pages/about-organization.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = TeamMember.objects.filter(year=self.request.current_edition.year).select_related('role', 'user')
        context['team'] = team
        context['team_pres'] = team.filter(role__rank=1).first()
        return context
