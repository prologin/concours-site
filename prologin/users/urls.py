from django.conf.urls import patterns, url
from users import views

urlpatterns = patterns('',
    url(r'^(?P<user_id>\d+)/activate/(?P<code>[0-9A-Za-z\-_]+)/$', views.activate, name='activate'),
    url(r'^(?P<user_id>\d+)/edit/$', views.edit_user, name='edit'),
    url(r'^(?P<user_id>\d+)/edit/password/$', views.edit_user_password, name='edit_password'),
    url(r'^(?P<pk>\d+)/profile/$', views.ProfileView.as_view(), name='profile'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'users/login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
    url(r'^register/$', views.register_view, name='register'),
)
