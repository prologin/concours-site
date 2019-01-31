from django.urls import include, path
from gcc import views, staff_views


app_name = 'gcc'

user_patterns = [
    path('profile', views.ProfileView.as_view(), name='profile'),
    path('edit', views.EditUserView.as_view(), name='edit'),
    path('edit/password', views.EditPasswordView.as_view(),
        name='edit_password'),
    path('delete', views.DeleteUserView.as_view(), name='delete'),
    path('takeout', views.TakeoutDownloadUserView.as_view(), name='takeout'),
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
        'review/<int:edition>/<int:event>/',
        staff_views.ApplicationReviewView.as_view(),
        name='application_review'),
    path(
        'form/<int:edition>/',
        views.ApplicationFormView.as_view(),
        name='application_form'),
    path(
        'validation/<int:edition>/',
        views.ApplicationValidation.as_view(),
        name='application_validation'),
    path(
        'summary/<int:pk>/',
        views.ApplicationSummaryView.as_view(),
        name='application_summary'),
    path(
        'label_remove/<int:event_id>/<int:applicant_id>/<int:label_id>/',
        staff_views.ApplicationRemoveLabelView.as_view(),
        name='delete_applicant_label'),
    path(
        'label_add/<int:event_id>/<int:applicant_id>/<int:label_id>/',
        staff_views.ApplicationAddLabelView.as_view(),
        name='add_applicant_label'),
]

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

    path('application/', include(application_patterns)),
    path('newsletter/', include(newsletter_patterns)),
    path('ressources/', views.RessourcesView.as_view(), name='ressources'),

    path('editions/', views.EditionsView.as_view(), name='editions'),
    path('editions/<int:year>/', views.EditionsView.as_view(), name='editions'),

    # User profile, view and edit
    path('user/<int:pk>/', include(user_patterns)),
    path('user/login', views.LoginView.as_view(), name='login'),
    path('user/register', views.RegistrationView.as_view(), name='register'),

]
