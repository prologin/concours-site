from django.urls import path, include
import contest.views
import contest.staff_views
import contest.interschool_views

app_name = 'contest'

correction_patterns = [
    path('', contest.staff_views.IndexView.as_view(), name='index'),
    path('<int:year>', contest.staff_views.YearIndexView.as_view(), name='year'),
    path('<int:year>/qualification', contest.staff_views.QualificationIndexView.as_view(), name='qualification'),
    path('<int:year>/semifinal', contest.staff_views.SemifinalIndexView.as_view(), name='semifinal'),
    path('<int:year>/semifinal/<int:event>', contest.staff_views.SemifinalEventIndexView.as_view(), name='semifinal'),
    path('<int:year>/final', contest.staff_views.FinalIndexView.as_view(), name='final'),
    path('<int:year>/<int:cid>/qualification', contest.staff_views.ContestantQualificationView.as_view(), name='contestant-qualification'),
    path('<int:year>/<int:cid>/semifinal', contest.staff_views.ContestantSemifinalView.as_view(), name='contestant-semifinal'),
    path('<int:year>/<int:cid>/live/<type>', contest.staff_views.ContestantLiveUpdate.as_view(), name='live-update'),
]

interschool_patterns = [
    path('leaderboard', contest.interschool_views.LeaderboardView.as_view(), name='leaderboard'),
]

urlpatterns = [
    path('<int:year>/qualification', contest.views.QualificationSummary.as_view(), name='qualification-summary'),
    path('inter-school-challenge/', include((interschool_patterns, app_name), namespace='interschool')),
    path('correct/', include((correction_patterns, app_name), namespace='correction')),
    path('semifinal/event-selection/', contest.views.ContestantSemifinalEventSelection.as_view(), name='semifinal-event-selection'),
]
