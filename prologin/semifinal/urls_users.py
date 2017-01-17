from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import TemplateView

import users.views

urlpatterns = [
    # Login and logout
    url(r'^login/$', users.views.custom_login, name='login'),
    url(r'^logout/$', users.views.protected_logout, {'next_page': '/'}, name='logout'),

    # Impersonate (django-hijack)
    url(r'^impersonate/search$', users.views.ImpersonateSearchView.as_view(), name='impersonate-search'),
    url(r'^impersonate$', users.views.ImpersonateView.as_view(), name='impersonate'),
]
