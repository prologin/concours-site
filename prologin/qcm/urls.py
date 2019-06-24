# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.urls import path

import qcm.views

app_name = 'qcm'

urlpatterns = [
    path('', qcm.views.DisplayQCMView.as_view(), name='display'),
]
