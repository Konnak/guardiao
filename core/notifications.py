"""
Sistema de notificações para o Sistema Guardião
"""
import requests
import os
from django.conf import settings
from django.utils import timezone
from .models import Guardian, Report
from bot.logging_config import log_system_event, log_error


class NotificationManager:
    """Gerenciador de notificações do sistema"""
    
    def __init__(self):
        self.bot_url = os.getenv('BOT_API_URL', 'http://localhost:8081')
        self.timeout = 10
    
    def notify_new_report(self, report):
        """Notifica Guardiões sobre nova denúncia"""
        try:
            online_guardians = Guardian.objects.filter(status='online')
            
            if not online_guardians.exists():
                return False
            
            guardian_ids = list(online_guardians.values_list('discord_id', flat=True))
            
            response = requests.post(
                f'{self.bot_url}/notify_guardians/',
                json={
                    'report_id': report.id,
                    'guardian_ids': guardian_ids,
                    'report_data': {
                        'reported_user_id': report.reported_user_id,
                        'reason': report.reason,
                        'guild_id': report.guild_id
                    }
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
    
    def notify_report_completed(self, report):
        """Notifica sobre denúncia concluída"""
        try:
            # Notificar o denunciante
            self._notify_user(
                report.reporter_user_id,
                f"Denúncia #{report.id} foi concluída",
                f"Sua denúncia contra o usuário {report.reported_user_id} foi processada."
            )
            
            # Notificar o usuário denunciado se foi punido
            if report.punishment != 'none':
                self._notify_user(
                    report.reported_user_id,
                    f"Você foi punido - Denúncia #{report.id}",
                    f"Você recebeu a seguinte punição: {report.get_punishment_display()}"
                )
            
            log_system_event("REPORT_COMPLETED_NOTIFIED", f"Report {report.id}")
            return True
            
        except Exception as e:
            log_error(f"Erro ao notificar conclusão da denúncia: {e}")
            return False
    
    def notify_appeal_created(self, appeal):
        """Notifica sobre nova apelação"""
        try:
            # Notificar administradores
            admin_guardians = Guardian.objects.filter(level__gte=4)  # Veteranos e Mestres
            
            for guardian in admin_guardians:
                self._notify_user(
                    guardian.discord_id,
                    f"Nova Apelação - Denúncia #{appeal.report.id}",
                    f"Uma nova apelação foi criada para a denúncia #{appeal.report.id}."
                )
            
            log_system_event("APPEAL_CREATED_NOTIFIED", f"Appeal for report {appeal.report.id}")
            return True
            
        except Exception as e:
            log_error(f"Erro ao notificar apelação: {e}")
            return False
    
    def notify_appeal_result(self, appeal):
        """Notifica sobre resultado da apelação"""
        try:
            if appeal.status == 'approved':
                message = f"Sua apelação da denúncia #{appeal.report.id} foi APROVADA. A punição foi revogada."
            else:
                message = f"Sua apelação da denúncia #{appeal.report.id} foi REJEITADA. A punição foi mantida."
            
            self._notify_user(
                appeal.appellant_user_id,
                f"Resultado da Apelação - Denúncia #{appeal.report.id}",
                message
            )
            
            log_system_event("APPEAL_RESULT_NOTIFIED", f"Appeal {appeal.id}, Status: {appeal.status}")
            return True
            
        except Exception as e:
            log_error(f"Erro ao notificar resultado da apelação: {e}")
            return False
    
    def _notify_user(self, user_id, title, message):
        """Notifica um usuário específico"""
        try:
            response = requests.post(
                f'{self.bot_url}/notify_user/',
                json={
                    'user_id': user_id,
                    'title': title,
                    'message': message
                },
                timeout=self.timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            log_error(f"Erro ao notificar usuário {user_id}: {e}")
            return False
    
    def notify_guardian_level_up(self, guardian, old_level, new_level):
        """Notifica Guardião sobre subida de nível"""
        try:
            self._notify_user(
                guardian.discord_id,
                f"🎉 Parabéns! Você subiu de nível!",
                f"Você subiu do nível {old_level} para o nível {new_level}! Continue o bom trabalho!"
            )
            
            log_system_event("GUARDIAN_LEVEL_UP_NOTIFIED", f"Guardian {guardian.id}: {old_level} -> {new_level}")
            return True
            
        except Exception as e:
            log_error(f"Erro ao notificar subida de nível: {e}")
            return False
    
    def notify_system_maintenance(self, message):
        """Notifica sobre manutenção do sistema"""
        try:
            all_guardians = Guardian.objects.all()
            
            for guardian in all_guardians:
                self._notify_user(
                    guardian.discord_id,
                    "🔧 Manutenção do Sistema",
                    message
                )
            
            log_system_event("MAINTENANCE_NOTIFIED", f"Message: {message}")
            return True
            
        except Exception as e:
            log_error(f"Erro ao notificar manutenção: {e}")
            return False


class ReportProcessor:
    """Processador de denúncias com notificações"""
    
    def __init__(self):
        self.notification_manager = NotificationManager()
    
    def process_report(self, report):
        """Processa uma denúncia completa"""
        try:
            # Calcular punição
            report.punishment = report.calculate_punishment()
            report.status = 'completed'
            report.completed_at = timezone.now()
            report.save()
            
            # Notificar sobre conclusão
            self.notification_manager.notify_report_completed(report)
            
            # Aplicar punição se necessário
            if report.punishment != 'none':
                self._apply_punishment(report)
            
            # Atualizar pontos dos Guardiões
            self._update_guardian_points(report)
            
            log_system_event("REPORT_PROCESSED", f"Report {report.id}, Punishment: {report.punishment}")
            return True
            
        except Exception as e:
            log_error(f"Erro ao processar denúncia: {e}")
            return False
    
    def _apply_punishment(self, report):
        """Aplica punição via bot"""
        try:
            response = requests.post(
                f'{self.notification_manager.bot_url}/apply_punishment/',
                json={
                    'report_id': report.id,
                    'punishment': report.punishment,
                    'user_id': report.reported_user_id,
                    'guild_id': report.guild_id
                },
                timeout=self.notification_manager.timeout
            )
            
            if response.status_code != 200:
                log_error(f"Falha ao aplicar punição para denúncia {report.id}")
                
        except Exception as e:
            log_error(f"Erro ao aplicar punição: {e}")
    
    def _update_guardian_points(self, report):
        """Atualiza pontos dos Guardiões"""
        try:
            votes = Vote.objects.filter(report=report)
            final_punishment = report.punishment
            
            for vote in votes:
                guardian = vote.guardian
                
                # Verificar se o voto foi correto
                vote_correct = self._is_vote_correct(vote.vote_type, final_punishment)
                
                if vote_correct:
                    guardian.correct_votes += 1
                    guardian.points += 1
                    
                    # Verificar se subiu de nível
                    old_level = guardian.level
                    self._update_guardian_level(guardian)
                    
                    if guardian.level > old_level:
                        self.notification_manager.notify_guardian_level_up(guardian, old_level, guardian.level)
                else:
                    guardian.incorrect_votes += 1
                
                guardian.save()
                
        except Exception as e:
            log_error(f"Erro ao atualizar pontos dos Guardiões: {e}")
    
    def _is_vote_correct(self, vote_type, final_punishment):
        """Verifica se um voto foi correto"""
        if final_punishment == 'none':
            return vote_type == 'improcedente'
        elif final_punishment in ['mute_1h', 'mute_12h']:
            return vote_type in ['intimidou', 'grave']
        elif final_punishment == 'ban_24h':
            return vote_type == 'grave'
        
        return False
    
    def _update_guardian_level(self, guardian):
        """Atualiza nível do Guardião baseado em pontos"""
        if guardian.points >= 1000:
            guardian.level = 5  # Mestre
        elif guardian.points >= 500:
            guardian.level = 4  # Veterano
        elif guardian.points >= 200:
            guardian.level = 3  # Experiente
        elif guardian.points >= 50:
            guardian.level = 2  # Aprendiz
        else:
            guardian.level = 1  # Novato


# Instâncias globais
notification_manager = NotificationManager()
report_processor = ReportProcessor()
