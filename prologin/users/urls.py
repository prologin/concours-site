import django.contrib.auth
from django.conf.urls import patterns, url
from users import views

urlpatterns = patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'users/login_message.html'}, name='login'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^register/$', views.register_view, name='register'),
    url(r'^profile/(?P<short_name>[0-9a-z_\-]+)/$', views.profile, name='profile'), # Reminder: \w doesn't match on hyphen (-), don't use it.
    url(r'^profile/(?P<short_name>[0-9a-z_\-]+)/avatar.png$', views.avatar, name='avatar'),
    url(r'^profile/(?P<short_name>[0-9a-z_\-]+)/avatar_(?P<scale>[a-z]+).png$', views.avatar, name='avatar_scale'),
)
