from django.views import generic
from team.models import TeamMember
import datetime


class AboutContestView(generic.TemplateView):
    template_name = 'pages/about-contest.html'


class AboutQualificationView(generic.TemplateView):
    template_name = 'pages/about-qualification.html'


class AboutSemifinalsView(generic.TemplateView):
    template_name = 'pages/about-semifinals.html'


class AboutFinalView(generic.TemplateView):
    template_name = 'pages/about-final.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base = self.request.current_events['final'].date_begin
        # We combine() because motherfucking Django's |date cannot datify date objects. Only datetime. FFS.
        # 4 is the number of days during the final
        context.update({'final_day{}'.format(d + 1): datetime.datetime.combine(base + datetime.timedelta(days=d), datetime.datetime.min.time())
                        for d in range(0, 4)})
        return context


class AboutOrganizationView(generic.TemplateView):
    template_name = 'pages/about-organization.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = TeamMember.objects.filter(year=self.request.current_edition.year).select_related('role', 'user')
        context['team'] = team
        context['team_pres'] = team.filter(role__id=1).first()
        return context
