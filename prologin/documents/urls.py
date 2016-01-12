from django.conf.urls import patterns, url


urlpatterns = patterns('documents.views',
    url(r'^(?P<year>[0-9]+)/(?P<center>[0-9]+|all)/convocations/$', 'generate_regionales_convocations'),
    url(r'^(?P<year>[0-9]+)/user/(?P<user>[0-9]+)/convocation/$', 'generate_regionales_user_convocation'),
    url(r'^(?P<year>[0-9]+)/(?P<center>[0-9]+|all)/userlist/$', 'generate_regionales_userlist'),
    url(r'^(?P<year>[0-9]+)/(?P<center>[0-9]+|all)/interviews/$', 'generate_regionales_interviews'),
    url(r'^(?P<year>[0-9]+)/(?P<center>[0-9]+|all)/passwords/$', 'generate_regionales_passwords'),
    url(r'^(?P<year>[0-9]+)/final/convocations/$', 'generate_finale_convocations'),
    url(r'^(?P<year>[0-9]+)/final/userlist/$', 'generate_finale_userlist'),
    url(r'^(?P<year>[0-9]+)/final/passwords/$', 'generate_finale_passwords'),
    url(r'^(?P<year>[0-9]+)/portrayal_agreement/$', 'generate_portrayal_agreement'),
)
