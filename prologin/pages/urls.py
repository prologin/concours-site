from django.urls import path
from pages import views

app_name = 'pages'

urlpatterns = [
    path('about/contest', views.AboutContestView.as_view(), name='about-contest'),
    path('about/contest/qualification', views.AboutQualificationView.as_view(), name='about-qualification'),
    path('about/contest/semifinals', views.AboutSemifinalsView.as_view(), name='about-semifinals'),
    path('about/contest/final', views.AboutFinalView.as_view(), name='about-final'),
    path('about/contest/history', views.AboutHistoryView.as_view(), name='about-history'),
    path('about/organization', views.AboutOrganizationView.as_view(), name='about-organization'),
    path('about/contest-rules', views.AboutContestRulesView.as_view(), name='about-contest-rules'),
    path('about/contribute', views.AboutContributeView.as_view(), name='about-contribute'),
]
