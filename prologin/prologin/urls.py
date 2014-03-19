from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from news import views

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'prologin.views.home', name='home'),
    # url(r'^prologin/', include('prologin.foo.urls')),
    url(r'^$', views.IndexView.as_view(), name='home'),
    url(r'^news/', include('news.urls', namespace='news')),
    url(r'^forum/', include('forum.urls', namespace='forum')),
    url(r'^user/', include('users.urls', namespace='users')),
    url(r'^page/', include('pages.urls', namespace='pages')),
    url(r'^team/', include('team.urls', namespace='team')),
    url(r'^documents/', include('documents.urls', namespace='docs')),
    url(r'^captcha/', include('captcha.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
