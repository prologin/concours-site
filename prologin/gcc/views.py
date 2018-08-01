from django.views.generic import TemplateView

# Photos

class PhotosIndexView(TemplateView):
    pass

class PhotosYearView(TemplateView):
    pass

class PhotosEditionView(TemplateView):
    pass

# Posters

class PostersView(TemplateView):
    pass

# Team

class TeamIndexView(TemplateView):
    pass

class TeamYearView(TemplateView):
    pass

# About

class AboutView(TemplateView):
    pass

# Homepage

class IndexView(TemplateView):
    template_name="gcc/index.html"
