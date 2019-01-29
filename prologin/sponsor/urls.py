from django.urls import path
import sponsor.views

app_name = 'sponsors'

urlpatterns = [
    path('', sponsor.views.IndexView.as_view(), name='index'),
]
