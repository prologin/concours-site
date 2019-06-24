# Copyright (C) <2013> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.urls import path

from team import views

app_name = 'team'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:year>', views.IndexView.as_view(), name='year'),
]
