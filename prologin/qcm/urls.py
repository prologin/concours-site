from django.conf.urls import url

import qcm.views

urlpatterns = [
    url(r'^$', qcm.views.DisplayQCMView.as_view(), name='display'),
]
