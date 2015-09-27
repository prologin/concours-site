import django.contrib.auth
from django.conf.urls import patterns, url
from forum import views

urlpatterns = patterns('',
    url(r'^(?!/api).*$', views.HomeTest, name='home'),
    #url(r'^$', views.HomeTest.as_view(), name='home'),
)
