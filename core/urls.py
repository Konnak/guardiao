"""
URLs para o Sistema Guardião
"""
from django.urls import path
from . import views

urlpatterns = [
    # Páginas principais
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reports/', views.reports_list, name='reports_list'),
    # path('report/<int:report_id>/', views.report_detail, name='report_detail'),  # REMOVIDO - expõe informações sensíveis
    
    # Sistema de Treinamento
    path('training/', views.training_start, name='training_start'),
    path('training/section/<int:section_id>/', views.training_section, name='training_section'),
    path('training/exercise/<int:exercise_id>/', views.training_exercise, name='training_exercise'),
    path('training/answer/<int:exercise_id>/', views.training_answer, name='training_answer'),
    
    # Autenticação
    path('auth/discord/', views.discord_login, name='discord_login'),
    path('auth/discord/callback/', views.discord_callback, name='discord_callback'),
    path('logout/', views.logout, name='logout'),
    
    # APIs
    path('api/vote/<int:report_id>/', views.VoteView.as_view(), name='api_vote'),
    path('api/status/', views.StatusToggleView.as_view(), name='api_status'),
]
