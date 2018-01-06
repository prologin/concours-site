from django.urls import path
import archives.views

app_name = 'archives'

urlpatterns = [
    path('', archives.views.Index.as_view(), name='index'),
    path('<int:year>/<type>/report', archives.views.Report.as_view(), name='report'),
    path('<int:year>/final/scoreboard', archives.views.FinalScoreboard.as_view(), kwargs={'type': 'final'}, name='finale-scoreboard'),
]
