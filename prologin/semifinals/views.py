from django.views.generic import TemplateView


class Homepage(TemplateView):
    template_name = 'semifinals/homepage.html'


class SemifinalSummary(TemplateView):
    template_name = 'semifinals/homepage.html'
