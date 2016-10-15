from django.conf.urls import url

import schools.views


urlpatterns = [
    url(r'^search$', schools.views.SchoolSearchView.as_view(), name='search'),
    url(r'^picture/(?P<pk>[0-9]+)$', schools.views.FacebookPictureView.as_view(), name='fb-picture'),
]
