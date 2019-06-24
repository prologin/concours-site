# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.urls import path
import sponsor.views

app_name = 'sponsors'

urlpatterns = [
    path('', sponsor.views.IndexView.as_view(), name='index'),
]
