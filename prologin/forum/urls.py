from django.conf.urls import url, include

from forum import views

thread_patterns = [
    url(r'^(?:(?P<slug>[\w-]+)-)(?P<pk>[0-9]+)/$', views.ThreadView.as_view(), name='thread'),
]

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^post/(?P<pk>[0-9]+)$', views.PostRedirectView.as_view(), name='post'),
    url(r'^(?:(?P<slug>[\w-]+)-)(?P<pk>[0-9]+)/$', views.ForumView.as_view(), name='forum'),

    url(r'^(?:(?P<forum_slug>[\w-]+)-)(?P<forum_pk>[0-9]+)/', include(thread_patterns)),
]
