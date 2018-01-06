from django.urls import path, include

import marauder.api_views
from marauder import views, api_views

app_name = 'marauder'

api_patterns = [
    # Location
    path('report', api_views.ApiReportView.as_view(), name='report'),
    path('geofences', api_views.ApiGeofencesView.as_view(), name='geofences'),

    # Data
    path('taskforces', marauder.api_views.ApiTaskForcesView.as_view(), name='taskforces'),
    path('event/settings', marauder.api_views.ApiEventSettingsView.as_view(), name='event-settings'),
    path('ping/user', marauder.api_views.ApiSendUserPingView.as_view(), name='ping-user'),
    path('ping/taskforce', marauder.api_views.ApiSendTaskforcePingView.as_view(), name='ping-taskforce'),
]

urlpatterns = [
    path('api/', include((api_patterns, app_name), namespace='api')),
    path('', views.IndexView.as_view(), name='index'),
]
