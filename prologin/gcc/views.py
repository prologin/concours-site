from django.views.generic import TemplateView

# Photos

class PhotosIndexView(TemplateView):
    template_name="gcc/photos_index.html"

class PhotosYearView(TemplateView):
    template_name="gcc/photos_year.html"

class PhotosEditionView(TemplateView):
    template_name="gcc/photos_edition.html"

# Posters

class PostersView(TemplateView):
    template_name="gcc/posters.html"

# Team

class TeamIndexView(TemplateView):
    template_name="gcc/team_index.html"

class TeamYearView(TemplateView):
    template_name="gcc/team_year.html"

# About

class AboutView(TemplateView):
    template_name="gcc/about.html"

# Homepage

class IndexView(TemplateView):
    template_name="gcc/index.html"
