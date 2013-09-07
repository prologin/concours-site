import django.contrib.auth
from django.conf.urls import patterns, url
from users import views

urlpatterns = patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'prologin/base.html'}, name='login'),
    url(r'^logout/$', views.logout_view, name='logout'),
)
