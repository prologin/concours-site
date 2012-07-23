from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from team.models import Team

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	(r'^centers/$', 'centers.views.index'),
	(r'^centers/json/(?P<ville>.*)$', 'centers.views.genjson'),
	(r'^centers/geocode$', 'centers.views.geocode'),
	(r'^team/$', 'team.views.list_team'),
	(r'^team/(?P<year>\d+)$', 'team.views.list_team'),
	(r'^documents/$', 'documents.views.gen_doc'),
    # Example:
    # (r'^admin/', include('admin.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
