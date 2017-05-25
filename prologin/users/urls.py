from django.conf.urls import url, include
from users import views

user_patterns = [
    url(r'profile/$', views.ProfileView.as_view(), name='profile'),
    url(r'edit/$', views.EditUserView.as_view(), name='edit'),
    url(r'edit/password/$', views.EditPasswordView.as_view(), name='edit_password'),

    # Homes
    url(r'home/(?P<year>[0-9]{4})/$', views.DownloadFinalHomeView.as_view(), name='download-final-home'),

    # Impersonate (django-hijack)
    url(r'impersonate$', views.ImpersonateView.as_view(), name='impersonate'),
]

urlpatterns = [
    # User profile, view and edit
    url(r'^(?P<pk>[0-9]+)/', include(user_patterns)),

    # Login and logout
    url(r'^login/$', views.custom_login, name='login'),
    url(r'^logout/$', views.protected_logout, {'next_page': '/'}, name='logout'),

    # Search
    url(r'^search/suggest$', views.UserSearchSuggestView.as_view(), name='search-suggest'),

    # Password reset
    url(r'^password/reset/ask/$', views.PasswordResetView.as_view(), name='password_reset'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'
    ),

    # Register and activate views
    url(r'^register/$', views.RegistrationView.as_view(), name='register'),
    url(r'^activate/(?P<slug>[0-9A-Za-z\-_]+)/$', views.ActivationView.as_view(), name='activate'),

    url(r'^unsubscribe/$', views.UnsubscribeView.as_view(), name='unsubscribe'),
]
