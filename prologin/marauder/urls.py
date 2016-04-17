from django.conf.urls import url, include

from marauder import views, api_views

api_patterns = [
    url(r'^report/$', api_views.report, name='report'),
    url(r'^geofences/$', api_views.geofences, name='geofences'),
]

urlpatterns = [
    url(r'^api/', include(api_patterns, namespace='api')),

    url(r'^$', views.IndexView.as_view(), name='index'),
]
