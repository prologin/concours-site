from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from zinnia.models import Entry
import qcm.models


def homepage(request):
    articles = Entry.published.prefetch_related('authors').all()[:settings.HOMEPAGE_ARTICLES]
    qcm_completed = None
    if request.current_qcm:
        qcm_completed = request.current_qcm.is_completed_for(request.current_contestant)
    return render(request, 'homepage/homepage.html', {
        'qcm_completed': qcm_completed,
        'born_year': settings.PROLOGIN_EDITION - settings.PROLOGIN_MAX_AGE,
        'articles': articles,
    })
