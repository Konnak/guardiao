"""
Comando para inicializar dados de teste do Sistema Guardião
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Guardian, Report, ReportQueue, Message


class Command(BaseCommand):
    help = 'Inicializa dados de teste para o Sistema Guardião'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a criação mesmo se já existirem dados',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Inicializando dados de teste...')
        
        # Criar Guardião de teste se não existir
        test_guardian, created = Guardian.objects.get_or_create(
            discord_id=1,
            defaults={
                'discord_username': 'TestUser',
                'discord_display_name': 'Usuário de Teste',
                'status': 'online',
                'level': 1,
                'points': 0,
                'total_service_hours': 0.0,
                'correct_votes': 0,
                'incorrect_votes': 0,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Guardião de teste criado: {test_guardian.discord_display_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Guardião de teste já existe: {test_guardian.discord_display_name}')
            )
        
        # Criar algumas denúncias de teste se não existirem
        if not Report.objects.exists() or options['force']:
            self.stdout.write('📝 Criando denúncias de teste...')
            
            # Denúncia 1
            report1 = Report.objects.create(
                guild_id=123456789,
                channel_id=987654321,
                reported_user_id=111111111,
                reporter_user_id=222222222,
                reason='Usuário enviou spam no canal',
                status='pending'
            )
            
            # Adicionar à fila
            ReportQueue.objects.create(
                report=report1,
                status='pending',
                priority=1
            )
            
            # Criar mensagens de exemplo
            Message.objects.create(
                report=report1,
                original_user_id=111111111,
                original_message_id=333333333,
                anonymized_username='Usuario***',
                content='Mensagem de spam repetida várias vezes',
                timestamp=timezone.now(),
                is_reported_user=True
            )
            
            # Denúncia 2
            report2 = Report.objects.create(
                guild_id=123456789,
                channel_id=987654321,
                reported_user_id=444444444,
                reporter_user_id=555555555,
                reason='Comportamento inadequado',
                status='pending'
            )
            
            ReportQueue.objects.create(
                report=report2,
                status='pending',
                priority=2
            )
            
            Message.objects.create(
                report=report2,
                original_user_id=444444444,
                original_message_id=666666666,
                anonymized_username='Usuario***',
                content='Conteúdo inadequado',
                timestamp=timezone.now(),
                is_reported_user=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Criadas {Report.objects.count()} denúncias de teste')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ Denúncias já existem. Use --force para recriar.')
            )
        
        # Estatísticas finais
        total_guardians = Guardian.objects.count()
        total_reports = Report.objects.count()
        pending_reports = Report.objects.filter(status='pending').count()
        queue_items = ReportQueue.objects.filter(status='pending').count()
        
        self.stdout.write('\n📊 Estatísticas do Sistema:')
        self.stdout.write(f'   • Total de Guardiões: {total_guardians}')
        self.stdout.write(f'   • Total de Denúncias: {total_reports}')
        self.stdout.write(f'   • Denúncias Pendentes: {pending_reports}')
        self.stdout.write(f'   • Itens na Fila: {queue_items}')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Inicialização concluída com sucesso!')
        )
