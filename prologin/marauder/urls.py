from django.conf.urls import url
from marauder import views

urlpatterns = [
    url(r'^report/$', views.report, name='report'),
]
