from django.conf.urls import patterns, include, url
from django.views.generic.list_detail import object_detail
from team.models import Team
from contest.models import Contestant
from django.contrib.auth.models import User

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	(r'^$', 'problems.views.index'),
	(r'^centers/$', 'centers.views.index'),
	(r'^centers/json/(?P<city>.*)$', 'centers.views.genjson'),
	(r'^centers/geocode$', 'centers.views.geocode'),
	(r'^team/$', 'team.views.list_team'),
	(r'^team/(?P<year>\d+)$', 'team.views.list_team'),
	(r'^documents/$', 'documents.views.gen_doc'),
	(r'^users/(?P<object_id>\d+)$', 'contest.views.get_profile'),
	(r'^export/$', 'documents.views.generate_convocations'),
	(r'^problems/$', 'problems.views.show_list_challenges'),
	(r'^problems/(?P<challenge>\w+)/$', 'problems.views.show_list_problems'),
	(r'^problems/(?P<challenge>\w+)/(?P<problem>.+)/$', 'problems.views.show_problem'),
	(r'^problems/(?P<challenge>\w+)/(?P<problem>.+)/trace/(?P<timestamp>\d+)$', 'problems.views.trace'),
	(r'^problems/(?P<challenge>\w+)/(?P<problem>.+)/traces$', 'problems.views.traces'),
    # Example:
    # (r'^admin/', include('admin.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
