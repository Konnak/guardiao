"""
Comando Django para verificar saúde do sistema
"""
from django.core.management.base import BaseCommand
from core.tasks import HealthCheckCommand


class Command(HealthCheckCommand):
    """Comando para verificar saúde do sistema"""
    pass
