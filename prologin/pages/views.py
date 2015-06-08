from django.views import generic
# from pages.models import Page
#
# class DetailView(generic.DetailView):
#     model = Page
#     template_name = 'pages/detail.html'


class AboutContestView(generic.TemplateView):
    template_name = 'pages/about.html'


class AboutOrganizationView(generic.TemplateView):
    template_name = 'pages/about.html'
