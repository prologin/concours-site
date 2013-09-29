from django.views import generic
from pages.models import Page

class DetailView(generic.DetailView):
    model = Page
    template_name = 'pages/detail.html'
