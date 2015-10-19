from django.conf.urls import url
import problems.views

urlpatterns = [
    url(r'^(?P<year>[0-9]{4})/(?P<type>[a-z\-]+)$',
        problems.views.Challenge.as_view(),
        name='challenge'),

    url(r'^(?P<year>[0-9]{4})/(?P<type>[a-z\-]+)/(?P<problem>[a-zA-Z0-9_.-]+)$',
        problems.views.Problem.as_view(),
        name='problem'),

    url(r'^(?P<year>[0-9]{4})/(?P<type>[a-z\-]+)/(?P<problem>[a-zA-Z0-9_.-]+)/lang-template$',
        problems.views.AjaxLanguageTemplate.as_view(),
        name='ajax-language-template'),

    url(r'^(?P<year>[0-9]{4})/(?P<type>[a-z\-]+)/(?P<problem>[a-zA-Z0-9_.-]+)/(?P<submission>[0-9]+)$',
        problems.views.SubmissionCode.as_view(),
        name='submission'),

    url(r'^submission-corrected/(?P<submission>[0-9]+)$',
        problems.views.AjaxSubmissionCorrected.as_view(),
        name='ajax-submission-corrected'),

    url(r'^search$', problems.views.SearchProblems.as_view(), name='search'),

    url(r'^$', problems.views.Index.as_view(), name='index'),
]
