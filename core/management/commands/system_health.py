"""
Comando para verificar a saúde do Sistema Guardião
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from core.models import Guardian, Report, ReportQueue, VotingSession, SessionGuardian


class Command(BaseCommand):
    help = 'Verifica a saúde do Sistema Guardião'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Verificando saúde do Sistema Guardião...\n')
        
        # Verificar conexão com banco de dados
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('✅ Conexão com banco de dados: OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro na conexão com banco: {e}'))
            return
        
        # Verificar modelos principais
        try:
            total_guardians = Guardian.objects.count()
            total_reports = Report.objects.count()
            total_queue_items = ReportQueue.objects.count()
            total_sessions = VotingSession.objects.count()
            
            self.stdout.write(f'📊 Estatísticas do Sistema:')
            self.stdout.write(f'   • Guardiões: {total_guardians}')
            self.stdout.write(f'   • Denúncias: {total_reports}')
            self.stdout.write(f'   • Itens na Fila: {total_queue_items}')
            self.stdout.write(f'   • Sessões de Votação: {total_sessions}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao consultar modelos: {e}'))
            return
        
        # Verificar Guardiões online
        try:
            online_guardians = Guardian.objects.filter(status='online').count()
            offline_guardians = Guardian.objects.filter(status='offline').count()
            
            self.stdout.write(f'\n👥 Status dos Guardiões:')
            self.stdout.write(f'   • Online: {online_guardians}')
            self.stdout.write(f'   • Offline: {offline_guardians}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar status dos Guardiões: {e}'))
        
        # Verificar denúncias por status
        try:
            pending_reports = Report.objects.filter(status='pending').count()
            voting_reports = Report.objects.filter(status='voting').count()
            completed_reports = Report.objects.filter(status='completed').count()
            
            self.stdout.write(f'\n📋 Status das Denúncias:')
            self.stdout.write(f'   • Pendentes: {pending_reports}')
            self.stdout.write(f'   • Em Votação: {voting_reports}')
            self.stdout.write(f'   • Concluídas: {completed_reports}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar status das denúncias: {e}'))
        
        # Verificar sessões ativas
        try:
            active_sessions = VotingSession.objects.filter(status='voting').count()
            waiting_sessions = VotingSession.objects.filter(status='waiting').count()
            completed_sessions = VotingSession.objects.filter(status='completed').count()
            
            self.stdout.write(f'\n🗳️ Status das Sessões:')
            self.stdout.write(f'   • Aguardando: {waiting_sessions}')
            self.stdout.write(f'   • Em Votação: {active_sessions}')
            self.stdout.write(f'   • Concluídas: {completed_sessions}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar sessões: {e}'))
        
        # Verificar problemas potenciais
        self.stdout.write(f'\n🔧 Verificações de Integridade:')
        
        # Verificar denúncias órfãs (sem fila)
        try:
            reports_without_queue = Report.objects.exclude(
                reportqueue__isnull=False
            ).count()
            
            if reports_without_queue > 0:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {reports_without_queue} denúncias sem entrada na fila')
                )
            else:
                self.stdout.write('✅ Todas as denúncias têm entrada na fila')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar fila: {e}'))
        
        # Verificar sessões órfãs (sem Guardiões)
        try:
            sessions_without_guardians = VotingSession.objects.exclude(
                sessionguardian__isnull=False
            ).count()
            
            if sessions_without_guardians > 0:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {sessions_without_guardians} sessões sem Guardiões')
                )
            else:
                self.stdout.write('✅ Todas as sessões têm Guardiões associados')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar sessões: {e}'))
        
        # Verificar Guardiões com discord_id duplicado
        try:
            from django.db.models import Count
            duplicate_guardians = Guardian.objects.values('discord_id').annotate(
                count=Count('discord_id')
            ).filter(count__gt=1)
            
            if duplicate_guardians.exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {duplicate_guardians.count()} discord_ids duplicados')
                )
            else:
                self.stdout.write('✅ Nenhum discord_id duplicado')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar duplicatas: {e}'))
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Verificação de saúde concluída!')
        )
