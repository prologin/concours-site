from django.conf.urls import patterns, include, url


urlpatterns = patterns('centers.views',
    url(r'^$', 'center_map', name='center_map'),
    url(r'^(?P<city>[a-z-]+)/json$', 'center_list_json'),
    url(r'^json$', 'center_list_json'),
)
