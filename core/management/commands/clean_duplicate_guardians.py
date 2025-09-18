from django.core.management.base import BaseCommand
from core.models import Guardian


class Command(BaseCommand):
    help = 'Limpa registros duplicados de Guardiões'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Procurando Guardiões duplicados...')
        
        # Encontrar discord_ids duplicados
        from django.db.models import Count
        duplicates = Guardian.objects.values('discord_id').annotate(
            count=Count('discord_id')
        ).filter(count__gt=1)
        
        if not duplicates:
            self.stdout.write('✅ Nenhum Guardião duplicado encontrado')
            return
        
        self.stdout.write(f'⚠️ Encontrados {len(duplicates)} discord_ids duplicados')
        
        total_deleted = 0
        for duplicate in duplicates:
            discord_id = duplicate['discord_id']
            guardians = Guardian.objects.filter(discord_id=discord_id).order_by('id')
            
            self.stdout.write(f'📋 Discord ID {discord_id}: {guardians.count()} registros')
            
            # Manter o primeiro registro (mais antigo) e deletar os outros
            keep_guardian = guardians.first()
            delete_guardians = guardians.exclude(id=keep_guardian.id)
            
            self.stdout.write(f'✅ Mantendo: {keep_guardian.discord_display_name} (ID: {keep_guardian.id})')
            
            for guardian in delete_guardians:
                self.stdout.write(f'🗑️ Deletando: {guardian.discord_display_name} (ID: {guardian.id})')
                guardian.delete()
                total_deleted += 1
        
        self.stdout.write(f'🎉 Limpeza concluída! {total_deleted} registros duplicados removidos')
