from django.urls import include, path
from gcc import views

app_name = 'gcc'

photos_patterns = [
    path('', views.PhotosIndexView.as_view(), name='photos_index'),
    path(
        '<int:edition>',
        views.PhotosEditionView.as_view(),
        name='photos_edition'),
    path(
        '<int:edition>/<int:event>',
        views.PhotosEventView.as_view(),
        name='photos_event'),
]

team_patterns = [
    path('', views.TeamIndexView.as_view(), name='team_index'),
    path(
        '<int:year>', views.TeamEditionView.as_view(), name='team_edition'),
]

newsletter_patterns = [
    path(
        'unsubscribe',
        views.NewsletterUnsubscribeView.as_view(),
        name='news_unsubscribe'),
    path(
        'unsubscribe_failed',
        views.NewsletterUnsubscribeView.as_view(
            extra_context={'fail':True}),
        name='news_unsubscribe_failed'),

    path(
        'confirm_subscribe',
        views.NewsletterConfirmSubscribeView.as_view(),
        name='news_confirm_subscribe'),
    path(
        'confirm_unsubscribe',
        views.NewsletterConfirmUnsubView.as_view(),
        name='news_confirm_unsub'),
]

application_patterns = [
    path(
        'review/',
        views.ApplicationIndexView.as_view(),
        name='application_index'),
    path(
        'form/<int:user_id>/',
        views.ApplicationForm.as_view(),
        name='application_form'),
    path(
        'validation/<int:user_id>/',
        views.ApplicationValidation.as_view(),
        name='application_validation'),
    path(
        'delete/<int:applicant_id>/<int:label_id>/',
        views.application_remove_label,
        name='delete_applicant_label'),
    path(
        'add/<int:applicant_id>/<int:label_id>/',
        views.application_add_label,
        name='add_applicant_label'),
]

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('ressources/', views.RessourcesView.as_view(), name='ressources'),
    path('editions/', views.EditionsView.as_view(), name='editions'),
    path('editions/<int:year>/', views.EditionsView.as_view(), name='editions'),
    path('team/', include(team_patterns)),
    path('photos/', include(photos_patterns)),
    path('newsletter/', include(newsletter_patterns)),
    path('application/', include(application_patterns))
]
