from django.urls import include, path
from gcc import views

app_name = 'gcc'

photos_patterns = [
    path('', views.PhotosIndexView.as_view(), name='photos_index'),
    path(
        '<int:edition>',
        views.PhotosEditionView.as_view(),
        name='photos_edition'),
    path(
        '<int:edition>/<int:event>',
        views.PhotosEventView.as_view(),
        name='photos_event'),
]

team_patterns = [
    path('', views.TeamIndexView.as_view(), name='team_index'),
    path(
        '<int:edition>', views.TeamEditionView.as_view(), name='team_edition'),
]

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about', views.AboutView.as_view(), name='about'),
    path('posters', views.PostersView.as_view(), name='posters'),
    path('team/', include(team_patterns)),
    path('photos/', include(photos_patterns)),
]
