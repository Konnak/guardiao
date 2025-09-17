#!/usr/bin/env python
"""
Script para iniciar o servidor Django na Discloud
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardiao.settings')

try:
    django.setup()
    print("✅ Django configurado com sucesso")
except Exception as e:
    print(f"❌ Erro ao configurar Django: {e}")
    sys.exit(1)

# Executar servidor Django
try:
    print("🚀 Iniciando servidor Django...")
    execute_from_command_line(['start_server.py', 'runserver', '0.0.0.0:8080'])
except Exception as e:
    print(f"❌ Erro ao iniciar servidor: {e}")
    sys.exit(1)
