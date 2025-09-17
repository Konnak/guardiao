#!/usr/bin/env python
"""Sistema Guardião - Gerenciador principal para site e bot Discord."""
import os
import sys
import asyncio
import threading
from django.core.management import execute_from_command_line
from django.conf import settings


def run_django_server():
    """Executa o servidor Django"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guardiao.settings")
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8080'])


def run_discord_bot():
    """Executa o bot Discord"""
    from bot.discord_bot import main as bot_main
    asyncio.run(bot_main())


def main():
    """Função principal que decide o que executar baseado nos argumentos"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'runserver':
            # Executa apenas o servidor Django
            run_django_server()
        elif command == 'runbot':
            # Executa apenas o bot Discord
            run_discord_bot()
        elif command == 'runall':
            # Executa ambos simultaneamente
            print("🚀 Iniciando Sistema Guardião...")
            print("📱 Servidor Django na porta 8080")
            print("🤖 Bot Discord")
            
            # Thread para o servidor Django
            django_thread = threading.Thread(target=run_django_server)
            django_thread.daemon = True
            django_thread.start()
            
            # Executa o bot Discord na thread principal
            run_discord_bot()
        else:
            # Comandos Django normais (migrate, createsuperuser, etc.)
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guardiao.settings")
            execute_from_command_line(sys.argv)
    else:
        # Sem argumentos, executa ambos
        print("🚀 Iniciando Sistema Guardião...")
        print("📱 Servidor Django na porta 8080")
        print("🤖 Bot Discord")
        
        # Thread para o servidor Django
        django_thread = threading.Thread(target=run_django_server)
        django_thread.daemon = True
        django_thread.start()
        
        # Executa o bot Discord na thread principal
        run_discord_bot()


if __name__ == "__main__":
    main()
