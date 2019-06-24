# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.urls import path
import problems.views

app_name = 'problems'

urlpatterns = [
    path('<int:year>/<type>', problems.views.Challenge.as_view(), name='challenge'),
    path('<int:year>/<type>/scoreboard', problems.views.ChallengeScoreboard.as_view(), name='challenge-scoreboard'),

    path('<int:year>/<type>/<problem>', problems.views.Problem.as_view(), name='problem'),
    path('<int:year>/<type>/<problem>/lang-template', problems.views.AjaxLanguageTemplate.as_view(), name='ajax-language-template'),
    path('<int:year>/<type>/<problem>/<int:submission>', problems.views.SubmissionCode.as_view(), name='submission'),

    path('submission-corrected/<int:submission>', problems.views.AjaxSubmissionCorrected.as_view(), name='ajax-submission-corrected'),
    path('submission-recorrect/<int:submission>', problems.views.RecorrectView.as_view(), name='submission-recorrect'),

    path('manual', problems.views.ManualView.as_view(), name='manual'),
    path('search', problems.views.SearchProblems.as_view(), name='search'),
    path('', problems.views.Index.as_view(), name='index'),
]
