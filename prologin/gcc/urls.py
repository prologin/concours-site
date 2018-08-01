from django.urls import include, path
from gcc import views

app_name = 'gcc'

photos_patterns = [
    path('', views.PhotosIndexView.as_view(), name='photos_index'),
    path('<int:year>', views.PhotosYearView.as_view(), name='photos_year'),
    path('<int:year>/<int:edition>', views.PhotosEditionView.as_view(), name='photos_edition'),
]

posters_patterns = [
    path('', views.TeamIndexView.as_view(), name='team_index'),
    path('<int:year>', views.TeamYearView.as_view(), name='team_year'),
]

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about', views.AboutView.as_view(), name='about'),
    path('posters', views.PostersView.as_view(), name='posters'),
    path('team/', include(posters_patterns)),
    path('photos/', include(photos_patterns)),
]
