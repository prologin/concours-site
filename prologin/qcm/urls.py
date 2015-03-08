from django.conf.urls import patterns, url, include
import qcm.views


urlpatterns = patterns('',
    url(r'^$', qcm.views.DisplayQCMView.as_view(), name='display'),
)
