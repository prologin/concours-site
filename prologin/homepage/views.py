from django.conf import settings
from django.shortcuts import render
from zinnia.models import Entry


def homepage(request):
    articles = Entry.published.prefetch_related('authors').all()[:settings.HOMEPAGE_ARTICLES]

    qcm_completed = None
    if request.current_qcm:
        qcm_completed = request.current_qcm.is_completed_for(request.current_contestant)

    problems_count = request.current_qcm_problems.count()
    problems_completed = request.current_contestant_qcm_problem_answers.count()

    return render(request, 'homepage/homepage.html', {
        'qcm_completed': qcm_completed,
        'problems_count': problems_count,
        'problems_completed': problems_completed,
        'born_year': settings.PROLOGIN_EDITION - settings.PROLOGIN_MAX_AGE,
        'articles': articles,
    })
