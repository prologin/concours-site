# Copyright (C) <2013> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.urls import path, re_path, include

import documents.views

app_name = 'documents'

semifinals_event_patterns = [
    path('convocations', documents.views.SemifinalConvocationsView.as_view(), name='convocations'),
    path('contestants', documents.views.SemifinalContestantsView.as_view(), name='contestants'),
    path('data-export', documents.views.SemifinalDataExportView.as_view(), name='data-export'),
    path('interviews', documents.views.SemifinalInterviewsView.as_view(), name='interviews'),
    path('passwords', documents.views.SemifinalPasswordsView.as_view(), name='passwords'),
]

semifinals_patterns = [
    path('contestant/<int:contestant>/convocation', documents.views.SemifinalContestantConvocationView.as_view(), name='contestant-convocation'),
    path('contestant/<int:contestant>/compilation', documents.views.SemifinalContestantCompilationView.as_view(), name='contestant-compilation'),
    path('portrayal-agreement', documents.views.SemifinalPortrayalAgreementView.as_view(), name='portrayal-agreement'),
    re_path(r'^(?P<event>[0-9]+|all)/', include(semifinals_event_patterns)),
]

final_patterns = [
    path('badges', documents.views.FinalBadgesView.as_view(), name='badges'),
    path('custom-badges', documents.views.FinalCustomBadgesView.as_view(), name='custom-badges'),
    path('custom-badges-input', documents.views.FinalCustomBadgesInputView.as_view(), name='custom-badges-input'),
    path('contestant/<int:contestant>/compilation', documents.views.FinalContestantCompilationView.as_view(), name='contestant-compilation'),
    path('contestant/<int:contestant>/convocation', documents.views.FinalContestantConvocationView.as_view(), name='contestant-convocation'),
    path('contestants', documents.views.FinalContestantsView.as_view(), name='contestants'),
    path('convocations', documents.views.FinalConvocationsView.as_view(), name='convocations'),
    path('data-export', documents.views.FinalDataExportView.as_view(), name='data-export'),
    path('diplomas', documents.views.FinalDiplomasView.as_view(), name='diplomas'),
    path('emergency-call-list', documents.views.FinalEmergencyCallListView.as_view(), name='emergency-call-list'),
    path('equipment-liability-release', documents.views.FinalEquipmentLiabilityReleaseView.as_view(), name='equipment-liability-release'),
    path('external-organizers', documents.views.FinalExternalOrganizersView.as_view(), name='external-organizers'),
    path('participation-authorization', documents.views.FinalParticipationAuthorizationView.as_view(), name='participation-authorization'),
    path('passwords', documents.views.FinalPasswordsView.as_view(), name='passwords'),
    path('planning', documents.views.FinalPlanningView.as_view(), name='planning'),
    path('portrayal-agreement', documents.views.FinalPortrayalAgreementView.as_view(), name='portrayal-agreement'),
    path('portrayal-agreement-orga', documents.views.FinalPortrayalAgreementOrgaView.as_view(), name='portrayal-agreement-orga'),
    path('meal-tickets', documents.views.FinalMealTicketsView.as_view(), name='meal-tickets'),
    path('meal-tickets-input', documents.views.FinalMealTicketsInputView.as_view(), name='meal-tickets-input'),
]

organization_patterns = [
    path('enrollment-form', documents.views.EnrollmentFormView.as_view(), name='enrollment-form'),
]

urlpatterns = [
    path('<int:year>/semifinal/', include((semifinals_patterns, app_name), namespace='semifinal')),
    path('<int:year>/final/', include((final_patterns, app_name), namespace='final')),
    path('<int:year>/organization/', include((organization_patterns, app_name), namespace='organization')),
    path('<int:year>', documents.views.IndexView.as_view(), name='index'),
    path('data-import/semifinal', documents.views.SemifinalDataImportView.as_view(), name='semifinal-data-import'),
    path('', documents.views.IndexRedirect.as_view(), name='index'),
]
