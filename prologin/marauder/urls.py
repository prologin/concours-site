from django.conf.urls import url
from marauder import views

urlpatterns = [
    url(r'^$', views.UI.as_view(), name='ui'),
    url(r'^api/report/$', views.report, name='report'),
    url(r'^api/geofences/$', views.geofences, name='geofences'),
]
