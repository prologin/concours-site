from django.conf.urls import url
from marauder import views

urlpatterns = [
    url(r'^$', views.UI.as_view(), name='ui'),
    url(r'^report/$', views.report, name='report'),
]
