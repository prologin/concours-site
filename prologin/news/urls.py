from django.conf.urls import url, include
from news.views import LegacyUrlRedirectView


urlpatterns = [
    url(r'^legacy/(?P<pk>[0-9]+)$', LegacyUrlRedirectView.as_view()),
    url(r'^', include('zinnia.urls', namespace='zinnia')),
]
