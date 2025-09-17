#!/usr/bin/env python
"""
Script para iniciar o servidor Django na Discloud
"""
import os
import sys
import django
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

# Executar servidor Django
try:
    print("🌐 Iniciando servidor Django na porta 8080...")
    print("=" * 60)
    execute_from_command_line(['start_server.py', 'runserver', '0.0.0.0:8080'])
except Exception as e:
    print(f"❌ Erro ao iniciar servidor: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
