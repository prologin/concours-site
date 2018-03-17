from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import TemplateView

import semifinal.staff_views
import semifinal.views
import users.views

app_name = 'prologin'

urlpatterns = [
    # Built-in Django admin
    path('admin/', admin.site.urls),

    # Language selector
    path('lang/', include('django.conf.urls.i18n')),
]

monitoring_patterns = [
    path('', semifinal.staff_views.MonitoringIndexView.as_view(), name='index'),
    path('unlock', semifinal.staff_views.ExplicitUnlockView.as_view(), name='unlock'),
]

users_patterns = [
    # Login and logout
    path('login', users.views.LoginView.as_view(), name='login'),
    path('logout', users.views.LogoutView.as_view(), {'next_page': '/'}, name='logout'),
]

urlpatterns += [
    # Homepage
    path('', semifinal.views.Homepage.as_view(), name='home'),

    # Live scoreboard
    path('scoreboard', semifinal.views.Scoreboard.as_view(), name='scoreboard'),
    path('scoreboard/data', semifinal.views.ScoreboardData.as_view(), name='scoreboard-data'),

    # Contest monitoring
    path('contest/monitor/', include((monitoring_patterns, app_name), namespace='monitoring')),

    # Contest
    path('contest/', include('contest.urls', namespace='contest')),

    # Semifinal problems
    path('semifinal/', include('problems.urls', namespace='problems')),

    path('user/', include((users_patterns, app_name), namespace='users')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path('e/400/', TemplateView.as_view(template_name='400.html')),
        path('e/403/', TemplateView.as_view(template_name='403.html')),
        path('e/404/', TemplateView.as_view(template_name='404.html')),
        path('e/500/', TemplateView.as_view(template_name='500.html')),
    ]
