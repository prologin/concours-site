from django.conf.urls import url, include

import marauder.api_views
from marauder import views, api_views

api_patterns = [
    # Location
    url(r'^report/$',
        api_views.ApiReportView.as_view(),
        name='report'),
    url(r'^geofences/$',
        api_views.ApiGeofencesView.as_view(),
        name='geofences'),

    # Data
    url('^taskforces/$',
        marauder.api_views.ApiTaskForcesView.as_view(),
        name='taskforces'),
    url('^event/settings/$',
        marauder.api_views.ApiEventSettingsView.as_view(),
        name='event-settings'),
    url('^ping/user/$',
        marauder.api_views.ApiSendUserPingView.as_view(),
        name='ping-user'),
    url('^ping/taskforce/$',
        marauder.api_views.ApiSendTaskforcePingView.as_view(),
        name='ping-taskforce'),
]

urlpatterns = [
    url(r'^api/', include(api_patterns, namespace='api')),
    url(r'^$', views.IndexView.as_view(),
        name='index'),
]
