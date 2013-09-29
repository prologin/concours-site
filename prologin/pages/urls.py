from django.conf.urls import patterns, url
from pages import views

urlpatterns = patterns('',
    url(r'^(?P<slug>[0-9a-z_\-]+)/$', views.DetailView.as_view(), name='show'), # Reminder: \w doesn't match on hyphen (-), don't use it.
)
