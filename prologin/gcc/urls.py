from django.urls import include, path
from gcc import views

app_name = 'gcc'

photos_patterns = [
    path('', views.PhotosIndexView.as_view(), name='photos_index'),
    path('<int:year>', views.PhotosYearView.as_view(), name='photos_year'),
    path('<int:year>/<int:edition>', views.PhotosEditionView.as_view(), name='photos_edition'),
]

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('photos/', include(photos_patterns)),
]
