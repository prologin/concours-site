from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
    url(r'^', include('zinnia.urls', namespace='zinnia')),
)
