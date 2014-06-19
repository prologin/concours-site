from django.conf.urls import patterns, url
from team import views

urlpatterns = patterns('',
    url(r'^(?P<year>\d+)/$', views.index, name='year'),
)
