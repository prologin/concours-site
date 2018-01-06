from django.urls import path

import qcm.views

app_name = 'qcm'

urlpatterns = [
    path('', qcm.views.DisplayQCMView.as_view(), name='display'),
]
