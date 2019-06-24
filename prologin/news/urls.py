# Copyright (C) <2013> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.urls import path, include
from news.views import LegacyUrlRedirectView

urlpatterns = [
    path('legacy/<int:pk>', LegacyUrlRedirectView.as_view()),
    path('', include('zinnia.urls', namespace='zinnia')),
]
