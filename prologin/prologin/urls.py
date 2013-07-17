from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'prologin.views.home', name='home'),
    # url(r'^prologin/', include('prologin.foo.urls')),
    url(r'^$', 'news.views.index', name='home'),
    url(r'^news/', include('news.urls', namespace='news')),
    url(r'^team/', include('team.urls', namespace='team')),
    url(r'^documents/', include('documents.urls', namespace='docs')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
