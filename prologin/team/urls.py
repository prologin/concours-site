from django.conf.urls import url

from team import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(),
        name='index'),
    url(r'^(?P<year>\d+)/$',
        views.IndexView.as_view(),
        name='year'),
]
