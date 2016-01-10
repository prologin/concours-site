from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import TemplateView

import semifinals.views


urlpatterns = [
    # Built-in Django admin
    url(r'^admin/', include(admin.site.urls)),

    # Language selector
    url(r'^lang/', include('django.conf.urls.i18n')),
]

urlpatterns += [
    # Homepage
    url(r'^$', semifinals.views.Homepage.as_view(), name='home'),
    url(r'^$', semifinals.views.SemifinalSummary.as_view(), name='semifinal_summary'),

    # Contest
    url(r'^contest/', include('contest.urls', namespace='contest')),

    # Semifinal problems
    url(r'^semifinal/', include('problems.urls', namespace='training')),

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
