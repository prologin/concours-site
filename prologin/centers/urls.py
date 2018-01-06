from django.urls import path

import centers.views

app_name = 'centers'

urlpatterns = [
    path('', centers.views.CenterListView.as_view(), name='map'),
]
