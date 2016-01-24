from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import TemplateView

import semifinal.staff_views
import semifinal.views


urlpatterns = [
    # Built-in Django admin
    url(r'^admin/', include(admin.site.urls)),

    # Language selector
    url(r'^lang/', include('django.conf.urls.i18n')),
]

monitoring_patterns = [
    url(r'^$', semifinal.staff_views.MonitoringIndexView.as_view(), name='index'),
    url(r'^unlock$', semifinal.staff_views.ExplicitUnlockView.as_view(), name='unlock'),
]

urlpatterns += [
    # Homepage
    url(r'^$', semifinal.views.Homepage.as_view(), name='home'),

    # Live scoreboard
    url(r'^scoreboard$', semifinal.views.Scoreboard.as_view(), name='scoreboard'),
    url(r'^scoreboard/data$', semifinal.views.ScoreboardData.as_view(), name='scoreboard-data'),

    # Contest monitoring
    url(r'^contest/monitor/', include(monitoring_patterns, namespace='monitoring')),

    # Contest
    url(r'^contest/', include('contest.urls', namespace='contest')),

    # Semifinal problems
    url(r'^semifinal/', include('problems.urls', namespace='problems')),

    # Authentication and accounts
    url(r'^user/', include('users.urls', namespace='users')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        url(r'^e/400/$', TemplateView.as_view(template_name='400.html')),
        url(r'^e/403/$', TemplateView.as_view(template_name='403.html')),
        url(r'^e/404/$', TemplateView.as_view(template_name='404.html')),
        url(r'^e/500/$', TemplateView.as_view(template_name='500.html')),
    ]
