from django.urls import path, include
from news.views import LegacyUrlRedirectView

urlpatterns = [
    path('legacy/<int:pk>', LegacyUrlRedirectView.as_view()),
    path('', include('zinnia.urls', namespace='zinnia')),
]
