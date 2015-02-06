from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
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
