from django.conf.urls import url
from pages import views

urlpatterns = [
    # url(r'^(?P<slug>[0-9a-z_\-]+)/$', views.DetailView.as_view(), name='show'), # Reminder: \w doesn't match on hyphen (-), don't use it.
    url(r'^about/contest$', views.AboutContestView.as_view(), name='about-contest'),
    url(r'^about/contest/qualification$', views.AboutQualificationView.as_view(), name='about-qualification'),
    url(r'^about/contest/semifinals', views.AboutSemifinalsView.as_view(), name='about-semifinals'),
    url(r'^about/contest/final', views.AboutFinalView.as_view(), name='about-final'),
    url(r'^about/organization', views.AboutOrganizationView.as_view(), name='about-organization'),
]
