# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.urls import path

import centers.views

app_name = 'centers'

urlpatterns = [
    path('', centers.views.CenterListView.as_view(), name='map'),
    path('<int:id>', centers.views.CenterDetailView.as_view(), name='detailMap')
]
