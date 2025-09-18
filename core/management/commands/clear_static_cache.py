from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil


class Command(BaseCommand):
    help = 'Limpa o cache de arquivos estáticos'

    def handle(self, *args, **options):
        self.stdout.write('🗑️ Limpando cache de arquivos estáticos...')
        
        # Limpar diretório de arquivos estáticos coletados
        static_root = settings.STATIC_ROOT
        if static_root and os.path.exists(static_root):
            try:
                shutil.rmtree(static_root)
                self.stdout.write(f'✅ Diretório {static_root} removido')
            except Exception as e:
                self.stdout.write(f'❌ Erro ao remover {static_root}: {e}')
        
        # Recriar diretório
        try:
            os.makedirs(static_root, exist_ok=True)
            self.stdout.write(f'✅ Diretório {static_root} recriado')
        except Exception as e:
            self.stdout.write(f'❌ Erro ao recriar {static_root}: {e}')
        
        self.stdout.write('🎉 Cache de arquivos estáticos limpo!')
        self.stdout.write('💡 Execute "python manage.py collectstatic" para recolher os arquivos')
