from django.core.management.base import BaseCommand
from core.models import Guardian
from django.utils import timezone


class Command(BaseCommand):
    help = 'Atualiza as datas de criação das contas Discord para usuários existentes'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Atualizando datas de criação das contas Discord...')
        
        updated_count = 0
        error_count = 0
        
        for guardian in Guardian.objects.filter(discord_account_created_at__isnull=True):
            try:
                # Converter Discord ID para timestamp
                discord_id = guardian.discord_id
                
                # Discord IDs são snowflakes que contêm timestamp de criação
                # Os primeiros 22 bits são o timestamp (em milissegundos desde 2015-01-01)
                timestamp_ms = (discord_id >> 22) + 1420070400000  # 1420070400000 é o epoch do Discord
                discord_account_created_at = timezone.datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                
                # Atualizar o Guardian
                guardian.discord_account_created_at = discord_account_created_at
                guardian.save()
                
                updated_count += 1
                
                self.stdout.write(
                    f'✅ {guardian.discord_display_name} (ID: {discord_id}) - '
                    f'Conta criada em: {discord_account_created_at.strftime("%d/%m/%Y %H:%M")}'
                )
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Erro ao atualizar {guardian.discord_display_name}: {e}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Atualização concluída!\n'
                f'✅ Atualizados: {updated_count}\n'
                f'❌ Erros: {error_count}'
            )
        )
