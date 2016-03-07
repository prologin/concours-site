from django.conf.urls import url

from team import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<year>\d+)/$', views.index, name='year'),
]
