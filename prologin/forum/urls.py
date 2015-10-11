import django.contrib.auth
from django.conf.urls import patterns, url
from forum import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^(?P<cat>\w+)/$', views.category, name='cat'),
    url(r'^(?P<cat>\w+)/(?P<pos>\w+)/$', views.post, name='post'),
)