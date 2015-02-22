from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Homepage
    url(r'^$', 'homepage.views.homepage', name='home'),

    # News (blog)
    url(r'^news/', include('news.urls')),

    # Teams
    url(r'^team/', include('team.urls', namespace='team')),

    # Centers
    url(r'^center/', include('centers.urls', namespace='centers')),

    # Documents
    url(r'^docs/', include('documents.urls', namespace='documents')),

    # Authentication and accounts
    url(r'^user/', include('users.urls', namespace='users')),

    # Captcha stuff
    # TODO: remove that
    url(r'^captcha/', include('captcha.urls')),

    # Built-in Django admin
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += patterns('',
        url(r'^e/400/$', TemplateView.as_view(template_name='400.html')),
        url(r'^e/403/$', TemplateView.as_view(template_name='403.html')),
        url(r'^e/404/$', TemplateView.as_view(template_name='404.html')),
        url(r'^e/500/$', TemplateView.as_view(template_name='500.html')),
    )
