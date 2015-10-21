from django.conf.urls import url, include

from forum import views

post_patterns = [
    url(r'^$', views.ThreadView.as_view(), name='thread'),
]

thread_patterns = [
    url(r'^new-thread', views.CreateThreadView.as_view(), name='create-thread'),
    url(r'^(?:(?P<slug>[\w-]+)-)(?P<pk>[0-9]+)/', include(post_patterns)),
]

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),

    # Permalink: sort non-standard pattern with decorative thread slug and just the post pk
    url(r'^post/(?P<thread_slug>[\w-]+)/(?P<pk>[0-9]+)$', views.PostRedirectView.as_view(), name='post'),
    url(r'^post/(?P<thread_slug>[\w-]+)/(?P<pk>[0-9]+)/edit$', views.EditPostView.as_view(), name='edit-post'),
    url(r'^post/(?P<thread_slug>[\w-]+)/(?P<pk>[0-9]+)/edit/visibility$', views.EditPostVisibilityView.as_view(), name='edit-post-visibility'),

    url(r'^(?:(?P<slug>[\w-]+)-)(?P<pk>[0-9]+)/$', views.ForumView.as_view(), name='forum'),

    url(r'^(?:(?P<forum_slug>[\w-]+)-)(?P<forum_pk>[0-9]+)/', include(thread_patterns)),
]
