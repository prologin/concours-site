from django.urls import path, re_path, include

import dashboard.views

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard.views.IndexView.as_view(), name='index'),
]
