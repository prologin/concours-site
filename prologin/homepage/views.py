from django.conf import settings
from django.shortcuts import render
from zinnia.models import Entry


def homepage(request):
    articles = Entry.published.all()[:settings.HOMEPAGE_ARTICLES]
    return render(request, 'homepage/homepage.html', {
        'articles': articles,
    })
