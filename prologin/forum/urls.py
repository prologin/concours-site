from django.urls import path, re_path, include

from forum import views

app_name = 'forum'

post_patterns = [
    path('', views.ThreadView.as_view(), name='thread'),
    path('edit/lock', views.EditThreadLockView.as_view(), name='edit-thread-lock'),
    path('edit/pin', views.EditThreadPinView.as_view(), name='edit-thread-pin'),
    path('edit/move', views.MoveThreadView.as_view(), name='move-thread'),
    path('delete', views.DeleteThreadView.as_view(), name='delete-thread'),
]

short_post_patterns = [
    path('', views.PostRedirectView.as_view(), name='post'),
    path('edit', views.EditPostView.as_view(), name='edit-post'),
    path('edit/visibility', views.EditPostVisibilityView.as_view(), name='edit-post-visibility'),
    path('cite', views.CitePostView.as_view(), name='cite-post'),
    path('delete', views.DeletePostView.as_view(), name='delete-post'),
]

thread_patterns = [
    # path('new-thread', views.CreateThreadView.as_view(), name='create-thread'),
    re_path(r'^(?:(?P<slug>[\w-]+)-)?(?P<pk>[0-9]+)/', include(post_patterns)),
]

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    re_path(r'^post/(?P<thread_slug>[\w-]+)/(?P<pk>[0-9]+)/', include(short_post_patterns)),
    re_path(r'^(?:(?P<slug>[\w-]+)-)?(?P<pk>[0-9]+)$', views.ForumView.as_view(), name='forum'),
    re_path(r'^(?:(?P<forum_slug>[\w-]+)-)?(?P<forum_pk>[0-9]+)/', include(thread_patterns)),
]
