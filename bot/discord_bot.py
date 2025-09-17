"""
Bot Discord para o Sistema Guardião
Gerencia comandos de denúncia e integração com o site Django
"""
import discord
from discord.ext import commands
import asyncio
import os
import sys
import django
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, List, Optional

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardiao.settings')
django.setup()

from core.models import Guardian, Report, Message


class MessageCache:
    """Cache para armazenar mensagens dos canais"""
    
    def __init__(self, max_messages_per_channel: int = 100, max_age_hours: int = 2):
        self.max_messages_per_channel = max_messages_per_channel
        self.max_age_hours = max_age_hours
        self.cache: Dict[int, List[discord.Message]] = {}
        self.last_cleanup = datetime.now()
    
    def add_message(self, message: discord.Message):
        """Adiciona uma mensagem ao cache"""
        channel_id = message.channel.id
        
        if channel_id not in self.cache:
            self.cache[channel_id] = []
        
        self.cache[channel_id].append(message)
        
        # Manter apenas as últimas N mensagens
        if len(self.cache[channel_id]) > self.max_messages_per_channel:
            self.cache[channel_id] = self.cache[channel_id][-self.max_messages_per_channel:]
        
        # Limpeza periódica
        self._cleanup_if_needed()
    
    def get_recent_messages(self, channel_id: int, count: int = 50) -> List[discord.Message]:
        """Retorna as mensagens mais recentes de um canal"""
        if channel_id not in self.cache:
            return []
        
        messages = self.cache[channel_id]
        return messages[-count:] if len(messages) >= count else messages
    
    def _cleanup_if_needed(self):
        """Remove mensagens antigas do cache"""
        now = datetime.now()
        if (now - self.last_cleanup).total_seconds() < 300:  # Limpeza a cada 5 minutos
            return
        
        cutoff_time = now - timedelta(hours=self.max_age_hours)
        
        for channel_id in list(self.cache.keys()):
            self.cache[channel_id] = [
                msg for msg in self.cache[channel_id]
                if msg.created_at.replace(tzinfo=None) > cutoff_time
            ]
            
            if not self.cache[channel_id]:
                del self.cache[channel_id]
        
        self.last_cleanup = now


class GuardiaoBot(commands.Bot):
    """Bot principal do Sistema Guardião"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.message_cache = MessageCache()
        self.site_url = os.getenv('SITE_URL', 'http://localhost:8080')
    
    async def on_ready(self):
        """Evento executado quando o bot está pronto"""
        print(f"🤖 Bot conectado como {self.user}")
        print(f"📊 Conectado em {len(self.guilds)} servidores")
        
        # Sincronizar comandos slash
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} comandos slash sincronizados")
        except Exception as e:
            print(f"❌ Erro ao sincronizar comandos: {e}")
    
    async def on_message(self, message):
        """Evento executado quando uma mensagem é enviada"""
        # Adicionar mensagem ao cache
        self.message_cache.add_message(message)
        
        # Processar comandos
        await self.process_commands(message)
    
    async def create_guardian_profile(self, user: discord.User) -> Guardian:
        """Cria um perfil de Guardião para um usuário"""
        guardian, created = Guardian.objects.get_or_create(
            discord_id=user.id,
            defaults={
                'discord_username': user.name,
                'discord_display_name': user.display_name or user.name,
                'avatar_url': str(user.avatar.url) if user.avatar else None,
            }
        )
        
        if not created:
            # Atualizar informações se já existir
            guardian.discord_username = user.name
            guardian.discord_display_name = user.display_name or user.name
            guardian.avatar_url = str(user.avatar.url) if user.avatar else None
            guardian.save()
        
        return guardian
    
    async def send_notification_to_guardians(self, report: Report):
        """Envia notificação para todos os Guardiões em serviço"""
        online_guardians = Guardian.objects.filter(status='online')
        
        for guardian in online_guardians:
            try:
                user = await self.fetch_user(guardian.discord_id)
                if user:
                    embed = discord.Embed(
                        title="🚨 Nova Denúncia Recebida",
                        description=f"Uma nova denúncia foi reportada e precisa de análise.",
                        color=0xff6b6b,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="Denúncia #" + str(report.id),
                        value=f"Usuário denunciado: <@{report.reported_user_id}>\nServidor: {report.guild_id}",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="Link para Análise",
                        value=f"[Clique aqui para analisar]({self.site_url}/report/{report.id}/)",
                        inline=False
                    )
                    
                    await user.send(embed=embed)
            except Exception as e:
                print(f"❌ Erro ao enviar notificação para {guardian.discord_display_name}: {e}")
    
    async def apply_punishment(self, report: Report):
        """Aplica a punição correspondente ao usuário"""
        try:
            guild = self.get_guild(report.guild_id)
            if not guild:
                print(f"❌ Servidor {report.guild_id} não encontrado")
                return
            
            user = guild.get_member(report.reported_user_id)
            if not user:
                print(f"❌ Usuário {report.reported_user_id} não encontrado no servidor")
                return
            
            punishment = report.punishment
            
            if punishment == 'mute_1h':
                # Implementar mute de 1 hora
                await self._apply_mute(user, 3600, "Denúncia aprovada - Mute de 1 hora")
            elif punishment == 'mute_12h':
                # Implementar mute de 12 horas
                await self._apply_mute(user, 43200, "Denúncia aprovada - Mute de 12 horas")
            elif punishment == 'ban_24h':
                # Implementar banimento de 24 horas
                await self._apply_temp_ban(user, 86400, "Denúncia aprovada - Banimento de 24 horas")
            
            # Notificar administradores para punições graves
            if punishment in ['ban_24h']:
                await self._notify_admins(guild, report, punishment)
                
        except Exception as e:
            print(f"❌ Erro ao aplicar punição: {e}")
    
    async def _apply_mute(self, user: discord.Member, duration: int, reason: str):
        """Aplica mute temporário"""
        # Implementar lógica de mute aqui
        print(f"🔇 Mute aplicado para {user.display_name}: {reason}")
    
    async def _apply_temp_ban(self, user: discord.Member, duration: int, reason: str):
        """Aplica banimento temporário"""
        # Implementar lógica de ban temporário aqui
        print(f"🔨 Ban aplicado para {user.display_name}: {reason}")
    
    async def _notify_admins(self, guild: discord.Guild, report: Report, punishment: str):
        """Notifica administradores sobre punições graves"""
        admins = [member for member in guild.members if member.guild_permissions.administrator]
        
        for admin in admins:
            try:
                embed = discord.Embed(
                    title="⚠️ Punição Grave Aplicada",
                    description=f"Uma punição grave foi aplicada em seu servidor.",
                    color=0xff4757,
                    timestamp=datetime.now()
                )
                
                embed.add_field(name="Usuário", value=f"<@{report.reported_user_id}>", inline=True)
                embed.add_field(name="Punição", value=punishment, inline=True)
                embed.add_field(name="Denúncia", value=f"#{report.id}", inline=True)
                
                await admin.send(embed=embed)
            except Exception as e:
                print(f"❌ Erro ao notificar admin {admin.display_name}: {e}")


# Instância global do bot
bot = GuardiaoBot()


@bot.tree.command(name="report", description="Reporta um usuário por violação das regras")
async def report_command(
    interaction: discord.Interaction,
    usuario: discord.Member,
    motivo: str = "Violação das regras do servidor"
):
    """Comando slash para reportar usuários"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Verificar se o usuário não está se reportando
        if usuario.id == interaction.user.id:
            await interaction.followup.send("❌ Você não pode se reportar!", ephemeral=True)
            return
        
        # Coletar mensagens recentes do canal
        recent_messages = bot.message_cache.get_recent_messages(interaction.channel.id, 50)
        
        # Criar denúncia no banco de dados
        report = Report.objects.create(
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            reported_user_id=usuario.id,
            reporter_user_id=interaction.user.id,
            reason=motivo,
            status='pending'
        )
        
        # Anonimizar e salvar mensagens
        user_mapping = {}
        user_counter = 1
        
        for msg in recent_messages:
            if msg.author.id not in user_mapping:
                if msg.author.id == usuario.id:
                    user_mapping[msg.author.id] = "Usuário Denunciado"
                elif msg.author.id == interaction.user.id:
                    user_mapping[msg.author.id] = "Denunciante"
                else:
                    user_mapping[msg.author.id] = f"Usuário {user_counter}"
                    user_counter += 1
            
            Message.objects.create(
                report=report,
                original_user_id=msg.author.id,
                original_message_id=msg.id,
                anonymized_username=user_mapping[msg.author.id],
                content=msg.content,
                timestamp=msg.created_at,
                is_reported_user=(msg.author.id == usuario.id)
            )
        
        # Notificar Guardiões em serviço
        await bot.send_notification_to_guardians(report)
        
        # Resposta para o usuário
        embed = discord.Embed(
            title="✅ Denúncia Enviada",
            description=f"Sua denúncia contra {usuario.display_name} foi enviada com sucesso!",
            color=0x2ed573,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Motivo", value=motivo, inline=False)
        embed.add_field(name="ID da Denúncia", value=f"#{report.id}", inline=True)
        embed.add_field(name="Status", value="Pendente de análise", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"❌ Erro no comando report: {e}")
        await interaction.followup.send("❌ Ocorreu um erro ao processar sua denúncia. Tente novamente.", ephemeral=True)


@bot.tree.command(name="status", description="Define seu status como Guardião")
async def status_command(
    interaction: discord.Interaction,
    status: str
):
    """Comando para Guardiões definirem seu status"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Criar ou atualizar perfil do Guardião
        guardian = await bot.create_guardian_profile(interaction.user)
        
        # Validar status
        if status.lower() not in ['online', 'offline', 'em-servico', 'fora-servico']:
            await interaction.followup.send("❌ Status inválido. Use: online, offline, em-servico ou fora-servico", ephemeral=True)
            return
        
        # Converter para formato do banco
        if status.lower() in ['online', 'em-servico']:
            guardian.status = 'online'
            status_display = "Em Serviço"
        else:
            guardian.status = 'offline'
            status_display = "Fora de Serviço"
        
        guardian.last_activity = datetime.now()
        guardian.save()
        
        embed = discord.Embed(
            title="📊 Status Atualizado",
            description=f"Seu status foi alterado para: **{status_display}**",
            color=0x2ed573 if guardian.status == 'online' else 0xff6b6b,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Nível", value=f"{guardian.level}", inline=True)
        embed.add_field(name="Pontos", value=f"{guardian.points}", inline=True)
        embed.add_field(name="Precisão", value=f"{guardian.accuracy_percentage}%", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"❌ Erro no comando status: {e}")
        await interaction.followup.send("❌ Ocorreu um erro ao atualizar seu status.", ephemeral=True)


async def main():
    """Função principal para executar o bot"""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN não encontrado nas variáveis de ambiente!")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
