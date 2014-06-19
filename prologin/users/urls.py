import django.contrib.auth
from django.conf.urls import patterns, url
from users import views

urlpatterns = patterns('',
    url(r'^activate/(?P<user_id>\d+)/(?P<code>[0-9A-Za-z\-_]+)/$', views.activate, name='activate'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'users/login.html'}, name='login'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^profile/(?P<pk>\d+)/$', views.ProfileView.as_view(), name='profile'),
    url(r'^register/$', views.register_view, name='register'),
)
