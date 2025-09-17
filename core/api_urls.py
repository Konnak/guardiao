"""
URLs da API para o Sistema Guardião
"""
from django.urls import path
from . import api_views

urlpatterns = [
    # Endpoints para o bot Discord
    path('reports/create/', api_views.create_report, name='api_create_report'),
    path('reports/<int:report_id>/', api_views.get_report_details, name='api_report_details'),
    path('punishments/apply/', api_views.apply_punishment, name='api_apply_punishment'),
    
    # Endpoints para votação
    path('votes/cast/', api_views.cast_vote, name='api_cast_vote'),
    
    # Endpoints para Guardiões
    path('guardians/online/', api_views.get_online_guardians, name='api_online_guardians'),
    path('guardians/status/', api_views.update_guardian_status, name='api_update_status'),
    
    # Endpoints para estatísticas
    path('stats/dashboard/', api_views.get_dashboard_stats, name='api_dashboard_stats'),
    
    # Endpoints para notificações em tempo real
    path('reports/check-new/', api_views.check_new_reports, name='api_check_new_reports'),
    
    # Endpoints para sistema de fila e modal
    path('guardian/<int:guardian_id>/pending-report/', api_views.get_pending_report_for_guardian, name='api_get_pending_report'),
    path('guardian/<int:guardian_id>/status/', api_views.get_guardian_status, name='api_get_guardian_status'),
    path('session/vote/', api_views.cast_vote_in_session, name='api_cast_vote_in_session'),
    path('session/leave/', api_views.leave_voting_session, name='api_leave_voting_session'),
    path('test/pending-reports/', api_views.test_pending_reports, name='api_test_pending_reports'),
]
