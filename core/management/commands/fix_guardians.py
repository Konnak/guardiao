"""
Comando para corrigir problemas com Guardiões no sistema
"""
from django.core.management.base import BaseCommand
from core.models import Guardian


class Command(BaseCommand):
    help = 'Corrige problemas com Guardiões no sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--discord-id',
            type=str,
            help='Discord ID específico para verificar',
        )
        parser.add_argument(
            '--list-all',
            action='store_true',
            help='Lista todos os Guardiões registrados',
        )

    def handle(self, *args, **options):
        self.stdout.write('🔍 Verificando Guardiões no sistema...\n')
        
        if options['list_all']:
            self.list_all_guardians()
        
        if options['discord_id']:
            self.check_specific_guardian(options['discord_id'])
        
        if not options['list_all'] and not options['discord_id']:
            self.check_guardians_integrity()

    def list_all_guardians(self):
        """Lista todos os Guardiões registrados"""
        guardians = Guardian.objects.all().order_by('discord_id')
        
        if not guardians.exists():
            self.stdout.write(self.style.WARNING('❌ Nenhum Guardião encontrado no sistema'))
            return
        
        self.stdout.write(f'📋 Guardiões registrados ({guardians.count()}):')
        self.stdout.write('-' * 80)
        
        for guardian in guardians:
            status_icon = '🟢' if guardian.status == 'online' else '🔴'
            self.stdout.write(
                f'{status_icon} {guardian.discord_display_name} '
                f'(ID: {guardian.discord_id}) - '
                f'Status: {guardian.get_status_display()} - '
                f'Nível: {guardian.level} - '
                f'Pontos: {guardian.points}'
            )
        
        self.stdout.write('-' * 80)

    def check_specific_guardian(self, discord_id):
        """Verifica um Guardião específico"""
        try:
            guardian = Guardian.objects.get(discord_id=discord_id)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Guardião encontrado: {guardian.discord_display_name} '
                    f'(ID: {guardian.discord_id})'
                )
            )
            self.stdout.write(f'   Status: {guardian.get_status_display()}')
            self.stdout.write(f'   Nível: {guardian.level}')
            self.stdout.write(f'   Pontos: {guardian.points}')
            self.stdout.write(f'   Criado em: {guardian.created_at}')
            self.stdout.write(f'   Última atividade: {guardian.last_activity}')
            
        except Guardian.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Guardião com ID {discord_id} não encontrado')
            )
            self.stdout.write('💡 Para registrar este usuário como Guardião:')
            self.stdout.write('   1. Acesse o site do sistema')
            self.stdout.write('   2. Faça login com Discord')
            self.stdout.write('   3. O sistema criará automaticamente o perfil')

    def check_guardians_integrity(self):
        """Verifica integridade dos Guardiões"""
        total_guardians = Guardian.objects.count()
        online_guardians = Guardian.objects.filter(status='online').count()
        offline_guardians = Guardian.objects.filter(status='offline').count()
        
        self.stdout.write(f'📊 Estatísticas dos Guardiões:')
        self.stdout.write(f'   • Total: {total_guardians}')
        self.stdout.write(f'   • Online: {online_guardians}')
        self.stdout.write(f'   • Offline: {offline_guardians}')
        
        # Verificar discord_ids duplicados
        from django.db.models import Count
        duplicates = Guardian.objects.values('discord_id').annotate(
            count=Count('discord_id')
        ).filter(count__gt=1)
        
        if duplicates.exists():
            self.stdout.write(
                self.style.WARNING(f'⚠️ {duplicates.count()} discord_ids duplicados encontrados')
            )
            for dup in duplicates:
                self.stdout.write(f'   Discord ID {dup["discord_id"]}: {dup["count"]} registros')
        else:
            self.stdout.write('✅ Nenhum discord_id duplicado')
        
        # Verificar Guardiões sem informações essenciais
        incomplete = Guardian.objects.filter(
            discord_username__isnull=True
        ).count()
        
        if incomplete > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠️ {incomplete} Guardiões com informações incompletas')
            )
        else:
            self.stdout.write('✅ Todos os Guardiões têm informações completas')
        
        self.stdout.write('\n💡 Comandos úteis:')
        self.stdout.write('   python manage.py fix_guardians --list-all')
        self.stdout.write('   python manage.py fix_guardians --discord-id 1369940071246991400')
