from django.conf.urls import patterns, url


urlpatterns = patterns('documents.views',
    url(r'^(?P<year>[0-9]+)/semifinals/(?P<center>[0-9]+|all)/convocations/$', 'generate_semifinals_convocations'),
    url(r'^(?P<year>[0-9]+)/semifinals/user/(?P<user>[0-9]+)/convocation/$', 'generate_semifinals_user_convocation'),
    url(r'^(?P<year>[0-9]+)/semifinals/(?P<center>[0-9]+|all)/userlist/$', 'generate_semifinals_userlist'),
    url(r'^(?P<year>[0-9]+)/semifinals/(?P<center>[0-9]+|all)/interviews/$', 'generate_semifinals_interviews'),
    url(r'^(?P<year>[0-9]+)/semifinals/(?P<center>[0-9]+|all)/passwords/$', 'generate_semifinals_passwords'),
    url(r'^(?P<year>[0-9]+)/semifinals/portrayal_agreement/$', 'generate_semifinals_portrayal_agreement'),

    url(r'^(?P<year>[0-9]+)/final/convocations/$', 'generate_final_convocations'),
    url(r'^(?P<year>[0-9]+)/final/user/(?P<user>[0-9]+)/convocation/$', 'generate_final_user_convocation'),
    url(r'^(?P<year>[0-9]+)/final/userlist/$', 'generate_finale_userlist'),
    url(r'^(?P<year>[0-9]+)/final/passwords/$', 'generate_finale_passwords'),
    url(r'^(?P<year>[0-9]+)/final/portrayal_agreement/$', 'generate_final_portrayal_agreement'),
)
