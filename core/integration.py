"""
Sistema de integração entre Django e Bot Discord
"""
import requests
import os
import json
from django.conf import settings
from .models import Report, Guardian, Vote
from bot.logging_config import log_system_event, log_error


class BotIntegration:
    """Classe para integração com o bot Discord"""
    
    def __init__(self):
        self.bot_url = os.getenv('BOT_API_URL', 'http://localhost:8081')
        self.timeout = 10
    
    def notify_guardians(self, report):
        """Notifica Guardiões online sobre nova denúncia"""
        try:
            online_guardians = Guardian.objects.filter(status='online')
            guardian_ids = list(online_guardians.values_list('discord_id', flat=True))
            
            if not guardian_ids:
                return False
            
            response = requests.post(
                f'{self.bot_url}/notify_guardians/',
                json={
                    'report_id': report.id,
                    'guardian_ids': guardian_ids
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                log_system_event("GUARDIANS_NOTIFIED", f"Report {report.id}, {len(guardian_ids)} guardians")
                return True
            else:
                log_error(f"Erro ao notificar Guardiões: {response.status_code}")
                return False
                
        except Exception as e:
            log_error(f"Erro ao notificar Guardiões: {e}")
            return False
    
    def apply_punishment(self, report):
        """Aplica punição via bot"""
        try:
            response = requests.post(
                f'{self.bot_url}/apply_punishment/',
                json={
                    'report_id': report.id,
                    'punishment': report.punishment,
                    'user_id': report.reported_user_id,
                    'guild_id': report.guild_id
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                log_system_event("PUNISHMENT_APPLIED", f"Report {report.id}, User {report.reported_user_id}")
                return True
            else:
                log_error(f"Erro ao aplicar punição: {response.status_code}")
                return False
                
        except Exception as e:
            log_error(f"Erro ao aplicar punição: {e}")
            return False
    
    def check_bot_health(self):
        """Verifica se o bot está funcionando"""
        try:
            response = requests.get(
                f'{self.bot_url}/health/',
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('status') == 'healthy'
            else:
                return False
                
        except Exception as e:
            log_error(f"Erro ao verificar saúde do bot: {e}")
            return False
    
    def get_bot_stats(self):
        """Obtém estatísticas do bot"""
        try:
            response = requests.get(
                f'{self.bot_url}/stats/',
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            log_error(f"Erro ao obter estatísticas do bot: {e}")
            return None


class ReportProcessor:
    """Classe para processar denúncias"""
    
    def __init__(self):
        self.bot_integration = BotIntegration()
    
    def process_report_completion(self, report):
        """Processa uma denúncia concluída"""
        try:
            # Calcular punição
            report.punishment = report.calculate_punishment()
            report.status = 'completed'
            report.save()
            
            # Aplicar punição se necessário
            if report.punishment != 'none':
                success = self.bot_integration.apply_punishment(report)
                if not success:
                    log_error(f"Falha ao aplicar punição para denúncia {report.id}")
            
            # Atualizar pontos dos Guardiões
            self.update_guardian_points(report)
            
            log_system_event("REPORT_COMPLETED", f"Report {report.id}, Punishment: {report.punishment}")
            return True
            
        except Exception as e:
            log_error(f"Erro ao processar conclusão da denúncia: {e}")
            return False
    
    def update_guardian_points(self, report):
        """Atualiza pontos dos Guardiões baseado no resultado"""
        try:
            votes = Vote.objects.filter(report=report)
            final_punishment = report.punishment
            
            for vote in votes:
                guardian = vote.guardian
                
                # Verificar se o voto foi correto
                vote_correct = self.is_vote_correct(vote.vote_type, final_punishment)
                
                if vote_correct:
                    guardian.correct_votes += 1
                    guardian.points += 1
                else:
                    guardian.incorrect_votes += 1
                
                guardian.save()
                
        except Exception as e:
            log_error(f"Erro ao atualizar pontos dos Guardiões: {e}")
    
    def is_vote_correct(self, vote_type, final_punishment):
        """Verifica se um voto foi correto baseado na punição final"""
        # Lógica para determinar se o voto foi correto
        if final_punishment == 'none':
            return vote_type == 'improcedente'
        elif final_punishment in ['mute_1h', 'mute_12h']:
            return vote_type in ['intimidou', 'grave']
        elif final_punishment == 'ban_24h':
            return vote_type == 'grave'
        
        return False


class GuardianManager:
    """Classe para gerenciar Guardiões"""
    
    def update_service_hours(self):
        """Atualiza horas de serviço dos Guardiões"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            # Guardiões que estavam online na última hora
            one_hour_ago = timezone.now() - timedelta(hours=1)
            online_guardians = Guardian.objects.filter(
                status='online',
                last_activity__gte=one_hour_ago
            )
            
            for guardian in online_guardians:
                guardian.total_service_hours += 1
                guardian.points += 1
                guardian.save()
            
            log_system_event("SERVICE_HOURS_UPDATED", f"{online_guardians.count()} guardians updated")
            
        except Exception as e:
            log_error(f"Erro ao atualizar horas de serviço: {e}")


# Instâncias globais
bot_integration = BotIntegration()
report_processor = ReportProcessor()
guardian_manager = GuardianManager()
