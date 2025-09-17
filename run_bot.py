#!/usr/bin/env python
"""
Script para executar apenas o bot Discord
"""
import os
import sys
import django
import asyncio

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardiao.settings')

try:
    print("⚙️ Configurando Django para o bot...")
    django.setup()
    print("✅ Django configurado com sucesso")
except Exception as e:
    print(f"❌ Erro ao configurar Django: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Executar bot Discord
try:
    print("🤖 Iniciando bot Discord...")
    from bot.discord_bot import main
    asyncio.run(main())
except Exception as e:
    print(f"❌ Erro ao executar bot Discord: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
