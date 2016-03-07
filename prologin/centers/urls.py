from django.conf.urls import url

import centers.views

urlpatterns = [
    url(r'^$', centers.views.CenterListView.as_view(), name='map'),
]
