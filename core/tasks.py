"""
Tasks para processamento automático do Sistema Guardião
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from .models import Report, Guardian, Vote
from .integration import report_processor, guardian_manager, bot_integration
from bot.logging_config import log_system_event, log_error


class ProcessReportsCommand(BaseCommand):
    """Comando para processar denúncias automaticamente"""
    
    help = 'Processa denúncias concluídas e atualiza estatísticas'
    
    def handle(self, *args, **options):
        """Executa o processamento"""
        try:
            self.process_completed_reports()
            self.update_guardian_stats()
            self.cleanup_old_data()
            
            self.stdout.write(
                self.style.SUCCESS('Processamento concluído com sucesso')
            )
            
        except Exception as e:
            log_error(f"Erro no processamento automático: {e}")
            self.stdout.write(
                self.style.ERROR(f'Erro: {e}')
            )
    
    def process_completed_reports(self):
        """Processa denúncias que foram concluídas mas não processadas"""
        try:
            # Denúncias com 5+ votos mas ainda em votação
            reports_to_process = Report.objects.filter(
                total_votes__gte=5,
                status='voting'
            )
            
            processed_count = 0
            for report in reports_to_process:
                if report_processor.process_report_completion(report):
                    processed_count += 1
            
            if processed_count > 0:
                log_system_event("REPORTS_PROCESSED", f"{processed_count} reports processed")
                self.stdout.write(f"Processadas {processed_count} denúncias")
            
        except Exception as e:
            log_error(f"Erro ao processar denúncias: {e}")
    
    def update_guardian_stats(self):
        """Atualiza estatísticas dos Guardiões"""
        try:
            guardian_manager.update_service_hours()
            self.stdout.write("Estatísticas dos Guardiões atualizadas")
            
        except Exception as e:
            log_error(f"Erro ao atualizar estatísticas: {e}")
    
    def cleanup_old_data(self):
        """Limpa dados antigos"""
        try:
            # Remover denúncias antigas (mais de 30 dias)
            cutoff_date = timezone.now() - timedelta(days=30)
            old_reports = Report.objects.filter(
                created_at__lt=cutoff_date,
                status='completed'
            )
            
            deleted_count = old_reports.count()
            old_reports.delete()
            
            if deleted_count > 0:
                log_system_event("OLD_DATA_CLEANED", f"{deleted_count} old reports deleted")
                self.stdout.write(f"Removidas {deleted_count} denúncias antigas")
            
        except Exception as e:
            log_error(f"Erro na limpeza de dados: {e}")


class HealthCheckCommand(BaseCommand):
    """Comando para verificar saúde do sistema"""
    
    help = 'Verifica a saúde do sistema e componentes'
    
    def handle(self, *args, **options):
        """Executa verificação de saúde"""
        try:
            self.check_database()
            self.check_bot_connection()
            self.check_reports_status()
            
            self.stdout.write(
                self.style.SUCCESS('Verificação de saúde concluída')
            )
            
        except Exception as e:
            log_error(f"Erro na verificação de saúde: {e}")
            self.stdout.write(
                self.style.ERROR(f'Erro: {e}')
            )
    
    def check_database(self):
        """Verifica conexão com banco de dados"""
        try:
            guardian_count = Guardian.objects.count()
            report_count = Report.objects.count()
            
            self.stdout.write(f"✅ Banco de dados: {guardian_count} Guardiões, {report_count} Denúncias")
            
        except Exception as e:
            self.stdout.write(f"❌ Erro no banco de dados: {e}")
    
    def check_bot_connection(self):
        """Verifica conexão com bot"""
        try:
            if bot_integration.check_bot_health():
                self.stdout.write("✅ Bot Discord: Conectado")
            else:
                self.stdout.write("❌ Bot Discord: Desconectado")
                
        except Exception as e:
            self.stdout.write(f"❌ Erro na conexão com bot: {e}")
    
    def check_reports_status(self):
        """Verifica status das denúncias"""
        try:
            pending = Report.objects.filter(status='pending').count()
            voting = Report.objects.filter(status='voting').count()
            completed = Report.objects.filter(status='completed').count()
            
            self.stdout.write(f"📊 Denúncias: {pending} Pendentes, {voting} Em Votação, {completed} Concluídas")
            
        except Exception as e:
            self.stdout.write(f"❌ Erro ao verificar denúncias: {e}")


def process_pending_reports():
    """Função para processar denúncias pendentes"""
    try:
        # Denúncias pendentes há mais de 1 hora
        one_hour_ago = timezone.now() - timedelta(hours=1)
        old_pending = Report.objects.filter(
            status='pending',
            created_at__lt=one_hour_ago
        )
        
        for report in old_pending:
            # Mover para votação se ainda não tem votos
            if report.total_votes == 0:
                report.status = 'voting'
                report.save()
                log_system_event("REPORT_MOVED_TO_VOTING", f"Report {report.id}")
        
        return old_pending.count()
        
    except Exception as e:
        log_error(f"Erro ao processar denúncias pendentes: {e}")
        return 0


def update_guardian_levels():
    """Atualiza níveis dos Guardiões baseado em pontos"""
    try:
        guardians = Guardian.objects.all()
        updated_count = 0
        
        for guardian in guardians:
            old_level = guardian.level
            
            # Calcular novo nível baseado em pontos
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
            
            if guardian.level != old_level:
                guardian.save()
                updated_count += 1
                log_system_event("GUARDIAN_LEVEL_UP", f"Guardian {guardian.id}: {old_level} -> {guardian.level}")
        
        return updated_count
        
    except Exception as e:
        log_error(f"Erro ao atualizar níveis dos Guardiões: {e}")
        return 0
