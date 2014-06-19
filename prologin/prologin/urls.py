from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='/team/2014/', permanent=False), name='home'), # To be changed
    url(r'^admin/', include(admin.site.urls)),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^user/', include('users.urls', namespace='users')),
    url(r'^team/', include('team.urls', namespace='team')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
