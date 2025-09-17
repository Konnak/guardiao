"""
Configuração de logging para o Sistema Guardião Bot
"""
import logging
import os
from datetime import datetime


def setup_logging():
    """Configura o sistema de logging para o bot"""
    
    # Criar diretório de logs se não existir
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar formato de log
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar logger principal
    logger = logging.getLogger('guardiao_bot')
    logger.setLevel(logging.INFO)
    
    # Remover handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para arquivo geral
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f'bot_{datetime.now().strftime("%Y%m%d")}.log'),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)
    
    # Handler para arquivo de erros
    error_handler = logging.FileHandler(
        os.path.join(log_dir, f'errors_{datetime.now().strftime("%Y%m%d")}.log'),
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # Adicionar handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    # Configurar logger do discord.py
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)
    
    # Configurar logger do Django
    django_logger = logging.getLogger('django')
    django_logger.setLevel(logging.WARNING)
    
    return logger


def log_report_created(report_id, user_id, reported_user_id, guild_id):
    """Log quando uma denúncia é criada"""
    logger = logging.getLogger('guardiao_bot')
    logger.info(f"DENÚNCIA CRIADA - ID: {report_id}, Usuário: {user_id}, Denunciado: {reported_user_id}, Servidor: {guild_id}")


def log_vote_cast(vote_id, guardian_id, report_id, vote_type):
    """Log quando um voto é registrado"""
    logger = logging.getLogger('guardiao_bot')
    logger.info(f"VOTO REGISTRADO - ID: {vote_id}, Guardião: {guardian_id}, Denúncia: {report_id}, Tipo: {vote_type}")


def log_punishment_applied(report_id, user_id, punishment_type, success):
    """Log quando uma punição é aplicada"""
    logger = logging.getLogger('guardiao_bot')
    status = "SUCESSO" if success else "FALHA"
    logger.info(f"PUNIÇÃO APLICADA - Denúncia: {report_id}, Usuário: {user_id}, Tipo: {punishment_type}, Status: {status}")


def log_guardian_status_change(guardian_id, old_status, new_status):
    """Log quando um Guardião muda de status"""
    logger = logging.getLogger('guardiao_bot')
    logger.info(f"STATUS ALTERADO - Guardião: {guardian_id}, De: {old_status}, Para: {new_status}")


def log_error(error_message, context=None):
    """Log de erros"""
    logger = logging.getLogger('guardiao_bot')
    if context:
        logger.error(f"ERRO - {error_message} - Contexto: {context}")
    else:
        logger.error(f"ERRO - {error_message}")


def log_system_event(event_type, details):
    """Log de eventos do sistema"""
    logger = logging.getLogger('guardiao_bot')
    logger.info(f"EVENTO SISTEMA - Tipo: {event_type}, Detalhes: {details}")
