from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import TemplateView
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Homepage
    url(r'^$', 'homepage.views.homepage', name='home'),

    # Captcha stuff
    # TODO: remove that
    url(r'^captcha/', include('captcha.urls')),

    # Built-in Django admin
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += i18n_patterns('',

    # News (blog)
    url(r'^news/', include('news.urls')),

    # Teams
    url(r'^team/', include('team.urls', namespace='team')),

    # Centers
    url(r'^center/', include('centers.urls', namespace='centers')),

    # Documents
    url(r'^docs/', include('documents.urls', namespace='documents')),

    # Contest
    # url(r'^contest/(?P<year>[0-9]{4})/regionale/problems/', include('problems.urls', namespace='training-regionale-problems')),
    url(r'^contest/(?P<year>[0-9]{4})/qualif/problems/', include('problems.urls', namespace='qcm-problems')),
    url(r'^contest/(?P<year>[0-9]{4})/qualif/quiz/', include('qcm.urls', namespace='qcm')),

    # Training
    url(r'^train/', include('problems.urls', namespace='training')),
    # url(r'^train/(?P<year>[0-9]{4})/qualif/problems/', include('problems.urls', namespace='training-qcm-problems')),
    # url(r'^train/(?P<year>[0-9]{4})/qualif/quiz/', include('problems.urls', namespace='training-qcm')),

    # Authentication and accounts
    url(r'^user/', include('users.urls', namespace='users')),

    # Pages
    url('^', include('pages.urls', namespace='pages')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += patterns('',
        url(r'^e/400/$', TemplateView.as_view(template_name='400.html')),
        url(r'^e/403/$', TemplateView.as_view(template_name='403.html')),
        url(r'^e/404/$', TemplateView.as_view(template_name='404.html')),
        url(r'^e/500/$', TemplateView.as_view(template_name='500.html')),
    )
