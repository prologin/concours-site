from django.conf.urls import url
import archives.views

urlpatterns = [
    url(r'^$', archives.views.Index.as_view(), name='index'),
    url(r'^(?P<year>[0-9]{4})/(?P<type>[a-z\-]+)/report$', archives.views.Report.as_view(), name='report'),
    url(r'^(?P<year>[0-9]{4})/final/scoreboard$', archives.views.FinalScoreboard.as_view(), kwargs={'type': 'final'}, name='finale-scoreboard'),
]
