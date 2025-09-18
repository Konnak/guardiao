from django.core.management.base import BaseCommand
from core.models import Guardian, Vote, SessionGuardian, VotingSession, ReportQueue


class Command(BaseCommand):
    help = 'Limpa todos os Guardiões cadastrados e dados relacionados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a exclusão de todos os dados',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING('⚠️ ATENÇÃO: Este comando irá deletar TODOS os Guardiões e dados relacionados!')
            )
            self.stdout.write('Para confirmar, execute: python manage.py clear_all_guardians --confirm')
            return

        self.stdout.write('🗑️ Iniciando limpeza completa dos Guardiões...')
        
        # Contar registros antes da limpeza
        guardians_count = Guardian.objects.count()
        votes_count = Vote.objects.count()
        session_guardians_count = SessionGuardian.objects.count()
        voting_sessions_count = VotingSession.objects.count()
        report_queues_count = ReportQueue.objects.count()
        
        self.stdout.write(f'📊 Registros encontrados:')
        self.stdout.write(f'   - Guardiões: {guardians_count}')
        self.stdout.write(f'   - Votos: {votes_count}')
        self.stdout.write(f'   - Sessões de Guardiões: {session_guardians_count}')
        self.stdout.write(f'   - Sessões de Votação: {voting_sessions_count}')
        self.stdout.write(f'   - Filas de Denúncias: {report_queues_count}')
        
        if guardians_count == 0:
            self.stdout.write('✅ Nenhum Guardião encontrado para deletar')
            return
        
        # Deletar dados relacionados primeiro (para evitar problemas de foreign key)
        self.stdout.write('🗑️ Deletando dados relacionados...')
        
        # Deletar votos
        Vote.objects.all().delete()
        self.stdout.write('   ✅ Votos deletados')
        
        # Deletar sessões de guardiões
        SessionGuardian.objects.all().delete()
        self.stdout.write('   ✅ Sessões de Guardiões deletadas')
        
        # Deletar sessões de votação
        VotingSession.objects.all().delete()
        self.stdout.write('   ✅ Sessões de Votação deletadas')
        
        # Deletar filas de denúncias
        ReportQueue.objects.all().delete()
        self.stdout.write('   ✅ Filas de Denúncias deletadas')
        
        # Deletar guardiões
        Guardian.objects.all().delete()
        self.stdout.write('   ✅ Guardiões deletados')
        
        # Verificar se tudo foi deletado
        remaining_guardians = Guardian.objects.count()
        remaining_votes = Vote.objects.count()
        remaining_sessions = VotingSession.objects.count()
        
        if remaining_guardians == 0 and remaining_votes == 0 and remaining_sessions == 0:
            self.stdout.write(
                self.style.SUCCESS('🎉 Limpeza concluída com sucesso!')
            )
            self.stdout.write('✅ Todos os Guardiões e dados relacionados foram removidos')
            self.stdout.write('💡 Agora você pode fazer login novamente para criar um novo perfil')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Erro na limpeza! Alguns registros ainda existem')
            )
            self.stdout.write(f'   - Guardiões restantes: {remaining_guardians}')
            self.stdout.write(f'   - Votos restantes: {remaining_votes}')
            self.stdout.write(f'   - Sessões restantes: {remaining_sessions}')
