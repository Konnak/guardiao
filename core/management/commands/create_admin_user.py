"""
Comando Django para criar um usuário administrador automaticamente
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Guardian


class Command(BaseCommand):
    help = 'Cria um usuário administrador do Django com ID do Discord'

    def add_arguments(self, parser):
        parser.add_argument(
            '--discord-id',
            type=str,
            default='1369940071246991380',
            help='ID do Discord do administrador (padrão: konnakrc)'
        )
        parser.add_argument(
            '--username',
            type=str,
            default='konnakrc',
            help='Nome de usuário do administrador'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@guardiao.com',
            help='Email do administrador'
        )

    def handle(self, *args, **options):
        discord_id = options['discord_id']
        username = options['username']
        email = options['email']
        
        self.stdout.write(f"🔧 Criando usuário administrador...")
        self.stdout.write(f"   Discord ID: {discord_id}")
        self.stdout.write(f"   Username: {username}")
        self.stdout.write(f"   Email: {email}")
        
        # Verificar se o usuário já existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"⚠️ Usuário '{username}' já existe!")
            )
            user = User.objects.get(username=username)
        else:
            # Criar novo usuário
            user = User.objects.create_user(
                username=username,
                email=email,
                password='admin123'  # Senha padrão - deve ser alterada
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ Usuário '{username}' criado com sucesso!")
            )
        
        # Tornar superusuário
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Usuário '{username}' configurado como superusuário!")
        )
        
        # Verificar se existe Guardian com esse Discord ID
        try:
            guardian = Guardian.objects.get(discord_id=int(discord_id))
            self.stdout.write(
                self.style.SUCCESS(f"✅ Guardian encontrado: {guardian.discord_display_name}")
            )
        except Guardian.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f"⚠️ Nenhum Guardian encontrado com Discord ID: {discord_id}")
            )
            self.stdout.write("   Execute o login via Discord para criar o Guardian automaticamente.")
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("🎉 Configuração de administrador concluída!"))
        self.stdout.write("\n📋 Informações de acesso:")
        self.stdout.write(f"   • URL Admin: /admin/")
        self.stdout.write(f"   • Username: {username}")
        self.stdout.write(f"   • Password: admin123")
        self.stdout.write(f"   • Discord ID: {discord_id}")
        self.stdout.write("\n⚠️ IMPORTANTE: Altere a senha padrão após o primeiro login!")
        self.stdout.write("=" * 50)
