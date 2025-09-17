#!/usr/bin/env python
"""
Script para iniciar o servidor Django e bot Discord na Discloud
"""
import os
import sys
import django
import subprocess
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

def run_discord_bot():
    """Executa o bot Discord em subprocess"""
    try:
        print("🤖 Iniciando bot Discord...")
        # Aguardar um pouco para o Django inicializar
        time.sleep(5)
        
        # Executar bot Discord usando script separado
        bot_process = subprocess.Popen([sys.executable, 'run_bot.py'])
        
        print("✅ Bot Discord iniciado em subprocess")
        return bot_process
    except Exception as e:
        print(f"❌ Erro ao iniciar bot Discord: {e}")
        import traceback
        traceback.print_exc()
        return None

# Iniciar bot Discord em subprocess primeiro
print("🚀 Iniciando Sistema Guardião completo...")
print("=" * 60)

bot_process = run_discord_bot()

# Executar servidor Django na thread principal
try:
    print("🌐 Iniciando servidor Django na porta 8080...")
    print("=" * 60)
    execute_from_command_line(['start_server.py', 'runserver', '0.0.0.0:8080'])
except KeyboardInterrupt:
    print("\n🛑 Sistema Guardião interrompido pelo usuário")
    if bot_process:
        bot_process.terminate()
    sys.exit(0)
except Exception as e:
    print(f"❌ Erro ao iniciar servidor Django: {e}")
    import traceback
    traceback.print_exc()
    if bot_process:
        bot_process.terminate()
    sys.exit(1)
