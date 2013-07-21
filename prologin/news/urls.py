from django.conf.urls import patterns, url
from news import views

urlpatterns = patterns('',
    url(r'^latest/(?P<offset>\d+)/(?P<nb>\d+)/$', views.latest, name='latest'),
    url(r'^(?P<pk>\d+)/$', views.DetailView.as_view(), name='show'),
    url(r'^latest.rss$', views.RSSView.as_view(), name='rss'),
)
