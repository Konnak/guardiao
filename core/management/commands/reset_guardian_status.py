from django.core.management.base import BaseCommand
from core.models import Guardian


class Command(BaseCommand):
    help = 'Coloca todos os Guardiões como offline'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Resetando status de todos os Guardiões...')
        
        # Contar guardiões online
        online_guardians = Guardian.objects.filter(status='online')
        offline_guardians = Guardian.objects.filter(status='offline')
        
        self.stdout.write(f'📊 Status atual:')
        self.stdout.write(f'   - Online: {online_guardians.count()}')
        self.stdout.write(f'   - Offline: {offline_guardians.count()}')
        
        if online_guardians.count() == 0:
            self.stdout.write('✅ Todos os Guardiões já estão offline')
            return
        
        # Colocar todos como offline
        updated_count = Guardian.objects.filter(status='online').update(status='offline')
        
        self.stdout.write(f'✅ {updated_count} Guardiões colocados como offline')
        self.stdout.write('🎉 Reset de status concluído!')
        self.stdout.write('💡 Agora você pode fazer login e entrar em serviço normalmente')
