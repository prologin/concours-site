from django.conf.urls import url
import contest.views
import contest.staff_views


urlpatterns = [
    url(r'^(?P<year>[0-9]{4})/qualification', contest.views.QualificationSummary.as_view(), name='qualification_summary'),
]

urlpatterns += [
    url(r'^correct/$', contest.staff_views.IndexView.as_view(), name='correction-index'),
    url(r'^correct/(?P<year>[0-9]{4})/$', contest.staff_views.YearIndexView.as_view(), name='correction-year'),
    url(r'^correct/(?P<year>[0-9]{4})/qualification$', contest.staff_views.QualificationIndexView.as_view(), name='correction-qualification'),
    url(r'^correct/(?P<year>[0-9]{4})/semifinal/(?P<event>[0-9]+)$', contest.staff_views.SemifinalIndexView.as_view(), name='correction-semifinal'),
    url(r'^correct/(?P<year>[0-9]{4})/(?P<cid>[0-9]+)/qualification$', contest.staff_views.ContestantQualificationView.as_view(), name='correction-contestant-qualification'),
    url(r'^correct/(?P<year>[0-9]{4})/(?P<cid>[0-9]+)/semifinal$', contest.staff_views.ContestantSemifinalView.as_view(), name='correction-contestant-semifinal'),
    url(r'^correct/(?P<year>[0-9]{4})/(?P<cid>[0-9]+)/live/(?P<type>[a-z]+)$', contest.staff_views.ContestantLiveUpdate.as_view(), name='correction-live-update'),
]