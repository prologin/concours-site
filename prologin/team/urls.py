from django.urls import path

from team import views

app_name = 'team'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:year>', views.IndexView.as_view(), name='year'),
]
