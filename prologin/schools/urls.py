from django.urls import path, re_path, include

import schools.views
import schools.admin_views

app_name = 'schools'

admin_patterns = [
    re_path(r'^merge/(?P<pks>[0-9,]+)$', schools.admin_views.MergeView.as_view(), name='merge')
]

urlpatterns = [
    path('search', schools.views.SchoolSearchView.as_view(), name='search'),
    path('picture/<int:pk>', schools.views.FacebookPictureView.as_view(), name='fb-picture'),
    path('admin/', include((admin_patterns, app_name), namespace='admin')),
]
