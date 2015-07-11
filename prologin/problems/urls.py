from django.conf.urls import url
import problems.views

urlpatterns = [
    url(r'^challenge/(?P<type>demi|qcm)(?P<year>[0-9]{4})$', problems.views.LegacyChallengeRedirect.as_view(), name='legacy-challenge'),
    url(r'^challenge/(?P<type>demi|qcm)(?P<year>[0-9]{4})/(?P<problem>[a-zA-Z0-9_-]+)$', problems.views.LegacyProblemRedirect.as_view(), name='legacy-problem'),

    url(r'^(?P<year>[0-9]{4})/(?P<type>[a-z\-]+)$', problems.views.Challenge.as_view(), name='challenge'),
    url(r'^(?P<year>[0-9]{4})/(?P<type>[a-z\-]+)/(?P<problem>[a-zA-Z0-9_-]+)$', problems.views.Problem.as_view(), name='problem'),

    url(r'^search$', problems.views.SearchProblems.as_view(), name='search'),
    url(r'^$', problems.views.Index.as_view(), name='index'),
]
