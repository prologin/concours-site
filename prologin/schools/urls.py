from django.conf.urls import url, include

import schools.views
import schools.admin_views

admin_patterns = [
    url(r'^merge/(?P<pks>[0-9,]+)$', schools.admin_views.MergeView.as_view(), name='merge')
]

urlpatterns = [
    url(r'^search$', schools.views.SchoolSearchView.as_view(), name='search'),
    url(r'^picture/(?P<pk>[0-9]+)$', schools.views.FacebookPictureView.as_view(), name='fb-picture'),
    url(r'^admin/', include(admin_patterns, namespace='admin')),
]
