"""
Comando Django para backup do sistema
"""
from django.core.management.base import BaseCommand
from core.backup import BackupCommand


class Command(BackupCommand):
    """Comando para backup do sistema"""
    pass
