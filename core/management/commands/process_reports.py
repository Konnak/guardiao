"""
Comando Django para processar denúncias automaticamente
"""
from django.core.management.base import BaseCommand
from core.tasks import ProcessReportsCommand


class Command(ProcessReportsCommand):
    """Comando para processar denúncias"""
    pass
