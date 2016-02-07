from django.conf.urls import url, include

import documents.views

semifinals_event_patterns = [
    url(r'^convocations$', documents.views.SemifinalConvocationsView.as_view(), name='convocations'),
    url(r'^contestants$', documents.views.SemifinalContestantsView.as_view(), name='contestants'),
    url(r'^data-export$', documents.views.SemifinalDataExportView.as_view(), name='data-export'),
    url(r'^interviews$', documents.views.SemifinalInterviewsView.as_view(), name='interviews'),
    url(r'^passwords$', documents.views.SemifinalPasswordsView.as_view(), name='passwords'),
]

semifinals_patterns = [
    url(r'^contestant/(?P<contestant>[0-9]+)/convocation$', documents.views.SemifinalContestantConvocationView.as_view(), name='contestant-convocation'),
    url(r'^contestant/(?P<contestant>[0-9]+)/compilation', documents.views.SemifinalContestantCompilationView.as_view(), name='contestant-compilation'),
    url(r'^portrayal-agreement$', documents.views.SemifinalPortrayalAgreementView.as_view(), name='portrayal-agreement'),
    url(r'^(?P<event>[0-9]+|all)/', include(semifinals_event_patterns)),
]

final_patterns = [
    url(r'^contestant/(?P<contestant>[0-9]+)/convocation$', documents.views.FinalContestantConvocationView.as_view(), name='contestant-convocation'),
    url(r'^contestant/(?P<contestant>[0-9]+)/compilation', documents.views.FinalContestantCompilationView.as_view(), name='contestant-compilation'),
    url(r'^portrayal-agreement$', documents.views.FinalPortrayalAgreementView.as_view(), name='portrayal-agreement'),
    url(r'^convocations$', documents.views.FinalConvocationsView.as_view(), name='convocations'),
    url(r'^contestants$', documents.views.FinalContestantsView.as_view(), name='contestants'),
    url(r'^passwords$', documents.views.FinalPasswordsView.as_view(), name='passwords'),
]

urlpatterns = [
    url(r'^(?P<year>[0-9]{4})/semifinal/', include(semifinals_patterns, namespace='semifinal')),
    url(r'^(?P<year>[0-9]{4})/final/', include(final_patterns, namespace='final')),
    url(r'^(?P<year>[0-9]{4})/$', documents.views.IndexView.as_view(), name='index'),
    url(r'^data-import/semifinal$', documents.views.SemifinalDataImportView.as_view(), name='semifinal-data-import'),
    url(r'^$', documents.views.IndexRedirect.as_view(), name='index'),
]
