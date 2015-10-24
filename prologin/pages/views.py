from django.views import generic

import datetime
import os
import yaml

from team.models import TeamMember


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
        current_final = self.request.current_events['final']
        if current_final:
            base = current_final.date_begin
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


class AboutHistoryView(generic.TemplateView):
    template_name = 'pages/about-history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            path = os.path.abspath(os.path.join(__file__, '../../prologin/settings/prologin-winners.yaml'))
            with open(path, encoding='utf-8') as f:
                context['winners'] = [{'year': year, 'name': name} for year, name in yaml.load(f).items()]
        except OSError:
            pass
        return context
