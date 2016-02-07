from django.conf.urls import url, include
import contest.views
import contest.staff_views


correction_patterns = [
    url(r'^$', contest.staff_views.IndexView.as_view(), name='index'),
    url(r'^(?P<year>[0-9]{4})/$', contest.staff_views.YearIndexView.as_view(), name='year'),
    url(r'^(?P<year>[0-9]{4})/qualification$', contest.staff_views.QualificationIndexView.as_view(), name='qualification'),
    url(r'^(?P<year>[0-9]{4})/semifinal/(?P<event>[0-9]+)$', contest.staff_views.SemifinalIndexView.as_view(), name='semifinal'),
    url(r'^(?P<year>[0-9]{4})/(?P<cid>[0-9]+)/qualification$', contest.staff_views.ContestantQualificationView.as_view(), name='contestant-qualification'),
    url(r'^(?P<year>[0-9]{4})/(?P<cid>[0-9]+)/semifinal$', contest.staff_views.ContestantSemifinalView.as_view(), name='contestant-semifinal'),
    url(r'^(?P<year>[0-9]{4})/(?P<cid>[0-9]+)/live/(?P<type>[a-z]+)$', contest.staff_views.ContestantLiveUpdate.as_view(), name='live-update'),
]

urlpatterns = [
    url(r'^(?P<year>[0-9]{4})/qualification', contest.views.QualificationSummary.as_view(), name='qualification_summary'),
    url(r'^correct/', include(correction_patterns, namespace='correction')),
]
