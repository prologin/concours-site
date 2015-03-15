from django.conf.urls import patterns, url
import problems.views

urlpatterns = patterns('',
    url(r'^$', problems.views.Index.as_view(), name='index'),
)
