from django.views.generic import TemplateView

# Photos

class PhotosIndexView(TemplateView):
    template_name="gcc/photos_index.html"

class PhotosEditionView(TemplateView):
    template_name="gcc/photos_edition.html"

class PhotosEventView(TemplateView):
    template_name="gcc/photos_event.html"

# Posters

class PostersView(TemplateView):
    template_name="gcc/posters.html"

# Team

class TeamIndexView(TemplateView):
    template_name="gcc/team_index.html"


class TeamEditionView(TemplateView):
    template_name="gcc/team_edition.html"

# About

class AboutView(TemplateView):
    template_name="gcc/about.html"

# Homepage

class IndexView(TemplateView):
    template_name="gcc/index.html"
