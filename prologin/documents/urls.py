from django.conf.urls import patterns, url, include
import documents.views

semifinals_center_patterns = [
    url(r'^convocations$', documents.views.SemifinalsConvocationsView.as_view(), name='semifinals-convocations'),
    url(r'^contestants$', documents.views.SemifinalsContestantsView.as_view(), name='semifinals-contestants'),
    url(r'^interviews$', documents.views.SemifinalsInterviewsView.as_view(), name='semifinals-interviews'),
    url(r'^passwords$', documents.views.SemifinalsPasswordsView.as_view(), name='semifinals-passwords'),
]

semifinals_patterns = [
    url(r'^portrayal-agreements$', documents.views.SemifinalsPortrayalAgreementView.as_view(), name='semifinals-portrayal-agreement'),
    url(r'^contestant/(?P<contestant>[0-9]+)/convocation$', documents.views.SemifinalsContestantConvocationView.as_view(), name='semifinals-contestant-convocation'),
    url(r'^contestant/(?P<contestant>[0-9]+)/compilation', documents.views.SemifinalsContestantCompilationView.as_view(), name='semifinals-contestant-compilation'),
    url(r'^(?P<center>[0-9]+|all)/', include(semifinals_center_patterns)),
]

final_patterns = [
    url(r'^portrayal-agreements$', documents.views.FinalPortrayalAgreementView.as_view(), name='final-portrayal-agreement'),
    url(r'^contestant/(?P<contestant>[0-9]+)/convocation$', documents.views.FinalContestantConvocationView.as_view(), name='final-contestant-convocation'),
    url(r'^contestant/(?P<contestant>[0-9]+)/compilation', documents.views.FinalContestantCompilationView.as_view(), name='final-contestant-compilation'),
    url(r'^convocations$', documents.views.FinalConvocationsView.as_view(), name='final-convocations'),
    url(r'^contestants$', documents.views.FinalContestantsView.as_view(), name='final-contestants'),
    url(r'^passwords$', documents.views.FinalsPasswordsView.as_view(), name='final-passwords'),
]

urlpatterns = [
    url(r'^(?P<year>[0-9]{4})/semifinals/', include(semifinals_patterns)),
    url(r'^(?P<year>[0-9]{4})/final/', include(final_patterns)),
    url(r'^$', documents.views.IndexView.as_view(), name='index'),
    url(r'^(?P<year>[0-9]{4})/$', documents.views.IndexView.as_view(), name='index'),
]
