#!/usr/bin/env python3
"""
Script de inicialização do Sistema Guardião
Executa todas as configurações necessárias para o funcionamento do sistema
"""
import os
import sys
import subprocess
import django
from pathlib import Path

# Adicionar o diretório do projeto ao Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardiao.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.core.management.commands.migrate import Command as MigrateCommand
from django.core.management.commands.collectstatic import Command as CollectStaticCommand


def run_command(command, description):
    """Executa um comando Django e exibe o resultado"""
    print(f"\n🔄 {description}...")
    try:
        execute_from_command_line(command.split())
        print(f"✅ {description} concluído com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao executar {description}: {e}")
        return False


def check_environment():
    """Verifica se as variáveis de ambiente estão configuradas"""
    print("🔍 Verificando configurações do ambiente...")
    
    required_vars = [
        'SECRET_KEY',
        'DISCORD_BOT_TOKEN',
        'DISCORD_CLIENT_ID',
        'DISCORD_CLIENT_SECRET',
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
        print("📝 Configure essas variáveis no arquivo .env ou discloud.env")
        return False
    
    print("✅ Todas as variáveis de ambiente necessárias estão configuradas")
    return True


def setup_database():
    """Configura o banco de dados"""
    print("\n🗄️ Configurando banco de dados...")
    
    # Executar migrações
    if not run_command("python manage.py migrate", "Executando migrações do banco"):
        return False
    
    return True


def setup_static_files():
    """Configura arquivos estáticos"""
    print("\n📁 Configurando arquivos estáticos...")
    
    # Coletar arquivos estáticos
    if not run_command("python manage.py collectstatic --noinput", "Coletando arquivos estáticos"):
        return False
    
    return True


def setup_test_data():
    """Configura dados de teste"""
    print("\n🧪 Configurando dados de teste...")
    
    # Inicializar dados de teste
    if not run_command("python manage.py init_test_data", "Inicializando dados de teste"):
        return False
    
    return True


def check_system_health():
    """Verifica a saúde do sistema"""
    print("\n🏥 Verificando saúde do sistema...")
    
    # Executar verificação de saúde
    if not run_command("python manage.py system_health", "Verificando saúde do sistema"):
        return False
    
    return True


def main():
    """Função principal do script de setup"""
    print("🚀 Iniciando configuração do Sistema Guardião...")
    print("=" * 60)
    
    # Verificar ambiente
    if not check_environment():
        print("\n❌ Configuração do ambiente falhou!")
        print("📝 Configure as variáveis de ambiente necessárias antes de continuar.")
        sys.exit(1)
    
    # Configurar banco de dados
    if not setup_database():
        print("\n❌ Configuração do banco de dados falhou!")
        sys.exit(1)
    
    # Configurar arquivos estáticos
    if not setup_static_files():
        print("\n❌ Configuração de arquivos estáticos falhou!")
        sys.exit(1)
    
    # Configurar dados de teste
    if not setup_test_data():
        print("\n❌ Configuração de dados de teste falhou!")
        sys.exit(1)
    
    # Verificar saúde do sistema
    if not check_system_health():
        print("\n❌ Verificação de saúde do sistema falhou!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Sistema Guardião configurado com sucesso!")
    print("\n📋 Próximos passos:")
    print("   1. Execute 'python start_server.py' para iniciar o servidor")
    print("   2. Execute 'python run_bot.py' para iniciar o bot Discord")
    print("   3. Acesse o sistema em: http://localhost:8080")
    print("\n🔧 Comandos úteis:")
    print("   • python manage.py system_health - Verificar saúde do sistema")
    print("   • python manage.py init_test_data --force - Recriar dados de teste")
    print("   • python manage.py shell - Abrir shell Django")
    print("=" * 60)


if __name__ == "__main__":
    main()
