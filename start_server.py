#!/usr/bin/env python
"""
Script para iniciar o servidor Django e bot Discord na Discloud
"""
import os
import sys
import django
import asyncio
import threading
import time
from django.core.management import execute_from_command_line

print("=" * 60)
print("🚀 SISTEMA GUARDIÃO - INICIANDO")
print("=" * 60)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardiao.settings')

try:
    print("⚙️ Configurando Django...")
    django.setup()
    print("✅ Django configurado com sucesso")
except Exception as e:
    print(f"❌ Erro ao configurar Django: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Executar migrações primeiro
try:
    print("📊 Executando migrações do banco de dados...")
    execute_from_command_line(['start_server.py', 'migrate', '--verbosity=2'])
    print("✅ Migrações executadas com sucesso")
except Exception as e:
    print(f"❌ Erro ao executar migrações: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Coletar arquivos estáticos
try:
    print("📁 Coletando arquivos estáticos...")
    execute_from_command_line(['start_server.py', 'collectstatic', '--clear', '--noinput', '--verbosity=2'])
    print("✅ Arquivos estáticos coletados com sucesso")
except Exception as e:
    print(f"❌ Erro ao coletar arquivos estáticos: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def run_django_server():
    """Executa o servidor Django"""
    try:
        print("🌐 Iniciando servidor Django na porta 8080...")
        execute_from_command_line(['start_server.py', 'runserver', '0.0.0.0:8080'])
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor Django: {e}")
        import traceback
        traceback.print_exc()

def run_discord_bot():
    """Executa o bot Discord"""
    try:
        print("🤖 Iniciando bot Discord...")
        # Aguardar um pouco para o Django inicializar
        time.sleep(5)
        
        # Importar e executar o bot
        from bot.discord_bot import main
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Erro ao iniciar bot Discord: {e}")
        import traceback
        traceback.print_exc()

# Iniciar Django e Discord Bot em threads separadas
print("🚀 Iniciando Sistema Guardião completo...")
print("=" * 60)

# Thread para Django
django_thread = threading.Thread(target=run_django_server, daemon=True)
django_thread.start()

# Thread para Discord Bot
bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
bot_thread.start()

# Aguardar threads
try:
    django_thread.join()
    bot_thread.join()
except KeyboardInterrupt:
    print("\n🛑 Sistema Guardião interrompido pelo usuário")
    sys.exit(0)
