from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.views.generic.base import TemplateView

import debug_toolbar

from homepage.views import HomepageView


def crash_test(request):
    if request.user.is_authenticated:
        1 / 0
    return HttpResponse(status=204)


urlpatterns = [
    # Debug toolbar
    path('__debug__/', include(debug_toolbar.urls)),

    # Homepage
    path('', HomepageView.as_view(), name='home'),

    # Built-in Django admin
    path('admin/', admin.site.urls),

    # Hijack
    path('hijack/', include('hijack.urls', namespace='hijack')),

    # Language selector
    path('lang/', include('django.conf.urls.i18n')),

    # News (blog)
    path('news/', include('news.urls')),

    # Forum
    path('forum/', include('forum.urls', namespace='forum')),

    # Teams
    path('team/', include('team.urls', namespace='team')),

    # Centers
    path('center/', include('centers.urls', namespace='centers')),

    # Documents
    path('docs/', include('documents.urls', namespace='documents')),

    # Archives
    path('archives/', include('archives.urls', namespace='archives')),

    # Contest
    path('contest/<int:year>/qualification/problems/', include('problems.urls', namespace='qcm-problems')),
    path('contest/<int:year>/qualification/quiz/', include('qcm.urls', namespace='qcm')),
    path('contest/', include('contest.urls', namespace='contest')),

    # Training
    path('train/', include('problems.urls', namespace='problems')),

    # Authentication and accounts
    path('user/', include('users.urls', namespace='users')),

    # Mailing
    path('mailing/', include('mailing.urls', namespace='mailing')),

    # Schools
    path('schools/', include('schools.urls', namespace='schools')),

    # Sponsors
    path('sponsors/', include('sponsor.urls', namespace='sponsors')),

    # Crash test
    path('crashtest/', crash_test),

    # Pages
    path('', include('pages.urls', namespace='pages')),

    # Monitoring
    path('', include('django_prometheus.urls')),
]

if settings.DEBUG:
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
    urlpatterns.extend([
        path('e/400/', TemplateView.as_view(template_name='400.html')),
        path('e/403/', TemplateView.as_view(template_name='403.html')),
        path('e/404/', TemplateView.as_view(template_name='404.html')),
        path('e/500/', TemplateView.as_view(template_name='500.html')),
    ])
