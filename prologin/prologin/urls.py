from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.views.generic.base import TemplateView

from homepage.views import HomepageView


def crash_test(request):
    if request.user.is_authenticated():
        1 / 0
    return HttpResponse(status=204)


urlpatterns = [
    # Homepage
    url(r'^$', HomepageView.as_view(), name='home'),

    # Built-in Django admin
    url(r'^admin/', include(admin.site.urls)),

    # Hijack
    url(r'^hijack/', include('hijack.urls')),

    # Language selector
    url(r'^lang/', include('django.conf.urls.i18n')),
]

urlpatterns += [
    # News (blog)
    url(r'^news/', include('news.urls')),

    # Forum
    url(r'^forum/', include('forum.urls', namespace='forum')),

    # Teams
    url(r'^team/', include('team.urls', namespace='team')),

    # Centers
    url(r'^center/', include('centers.urls', namespace='centers')),

    # Documents
    url(r'^docs/', include('documents.urls', namespace='documents')),

    # Archives
    url(r'^archives/', include('archives.urls', namespace='archives')),

    # Contest
    url(r'^contest/(?P<year>[0-9]{4})/qualification/problems/', include('problems.urls', namespace='qcm-problems')),
    url(r'^contest/(?P<year>[0-9]{4})/qualification/quiz/', include('qcm.urls', namespace='qcm')),
    url(r'^contest/', include('contest.urls', namespace='contest')),

    # Training
    url(r'^train/', include('problems.urls', namespace='problems')),

    # Authentication and accounts
    url(r'^user/', include('users.urls', namespace='users')),

    # Marauder UI and API.
    url(r'^marauder/', include('marauder.urls', namespace='marauder')),

    # Mailing
    url(r'^mailing/', include('mailing.urls', namespace='mailing')),

    # Schools
    url(r'^schools/', include('schools.urls', namespace='schools')),

    # Crash test
    url(r'^crashtest/', crash_test),

    # Pages
    url(r'^', include('pages.urls', namespace='pages')),

    # Monitoring
    url('', include('django_prometheus.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        url(r'^e/400/$', TemplateView.as_view(template_name='400.html')),
        url(r'^e/403/$', TemplateView.as_view(template_name='403.html')),
        url(r'^e/404/$', TemplateView.as_view(template_name='404.html')),
        url(r'^e/500/$', TemplateView.as_view(template_name='500.html')),
    ]
