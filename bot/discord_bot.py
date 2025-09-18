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
from bot.logging_config import setup_logging, log_report_created, log_vote_cast, log_punishment_applied, log_guardian_status_change, log_error, log_system_event

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardiao.settings')
try:
    django.setup()
except Exception as e:
    print(f"Erro ao configurar Django: {e}")

from core.models import Guardian, Report, Message, ReportQueue


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
        
        # Log do evento
        log_system_event("BOT_STARTED", f"Conectado como {self.user}, Servidores: {len(self.guilds)}")
        
        # Sincronizar comandos slash
        try:
            # Aguardar um pouco para garantir que o bot está totalmente conectado
            await asyncio.sleep(2)
            
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} comandos slash sincronizados")
            print("📋 Comandos disponíveis:")
            for cmd in synced:
                print(f"   - /{cmd.name}: {cmd.description}")
            
            log_system_event("COMMANDS_SYNCED", f"{len(synced)} comandos sincronizados")
        except Exception as e:
            print(f"❌ Erro ao sincronizar comandos: {e}")
            log_error(f"Erro ao sincronizar comandos: {e}")
            
            # Tentar novamente após 5 segundos
            try:
                await asyncio.sleep(5)
                synced = await self.tree.sync()
                print(f"✅ Segunda tentativa: {len(synced)} comandos sincronizados")
            except Exception as e2:
                print(f"❌ Segunda tentativa falhou: {e2}")
                log_error(f"Segunda tentativa de sincronização falhou: {e2}")
    
    async def on_message(self, message):
        """Evento executado quando uma mensagem é enviada"""
        # Adicionar mensagem ao cache
        self.message_cache.add_message(message)
        
        # Processar comandos
        await self.process_commands(message)
    
    async def create_guardian_profile(self, user: discord.User) -> Guardian:
        """Cria um perfil de Guardião para um usuário"""
        from asgiref.sync import sync_to_async
        
        guardian, created = await sync_to_async(Guardian.objects.get_or_create)(
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
            await sync_to_async(guardian.save)()
        
        return guardian
    
    async def send_notification_to_guardians(self, report: Report):
        """Envia notificação para todos os Guardiões em serviço"""
        from asgiref.sync import sync_to_async
        
        online_guardians = await sync_to_async(list)(Guardian.objects.filter(status='online'))
        
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
                return False
            
            user = guild.get_member(report.reported_user_id)
            if not user:
                print(f"❌ Usuário {report.reported_user_id} não encontrado no servidor")
                return False
            
            punishment = report.punishment
            success = False
            
            if punishment == 'mute_1h':
                success = await self._apply_mute(user, 3600, "Denúncia aprovada - Mute de 1 hora")
            elif punishment == 'mute_12h':
                success = await self._apply_mute(user, 43200, "Denúncia aprovada - Mute de 12 horas")
            elif punishment == 'ban_24h':
                success = await self._apply_temp_ban(user, 86400, "Denúncia aprovada - Banimento de 24 horas")
            
            # Notificar administradores para punições graves
            if punishment in ['ban_24h'] and success:
                await self._notify_admins(guild, report, punishment)
            
            return success
                
        except Exception as e:
            print(f"❌ Erro ao aplicar punição: {e}")
            return False
    
    async def _apply_mute(self, user: discord.Member, duration: int, reason: str):
        """Aplica mute temporário"""
        try:
            # Verificar se o bot tem permissão para mutar
            if not user.guild.me.guild_permissions.mute_members:
                print(f"❌ Bot não tem permissão para mutar no servidor {user.guild.name}")
                return False
            
            # Aplicar timeout (mute temporário)
            await user.timeout(discord.utils.timedelta(seconds=duration), reason=reason)
            print(f"🔇 Mute aplicado para {user.display_name}: {reason}")
            
            # Enviar DM para o usuário
            try:
                embed = discord.Embed(
                    title="🔇 Você foi mutado",
                    description=f"Você foi mutado por {duration//3600} hora(s) devido a uma denúncia aprovada.",
                    color=0xff6b6b,
                    timestamp=datetime.now()
                )
                embed.add_field(name="Motivo", value=reason, inline=False)
                embed.add_field(name="Duração", value=f"{duration//3600} hora(s)", inline=True)
                await user.send(embed=embed)
            except:
                pass  # Usuário pode ter DMs desabilitadas
            
            return True
        except Exception as e:
            print(f"❌ Erro ao aplicar mute: {e}")
            return False
    
    async def _apply_temp_ban(self, user: discord.Member, duration: int, reason: str):
        """Aplica banimento temporário"""
        try:
            # Verificar se o bot tem permissão para banir
            if not user.guild.me.guild_permissions.ban_members:
                print(f"❌ Bot não tem permissão para banir no servidor {user.guild.name}")
                return False
            
            # Enviar DM antes do ban
            try:
                embed = discord.Embed(
                    title="🔨 Você foi banido",
                    description=f"Você foi banido por {duration//3600} hora(s) devido a uma denúncia grave aprovada.",
                    color=0xff4757,
                    timestamp=datetime.now()
                )
                embed.add_field(name="Motivo", value=reason, inline=False)
                embed.add_field(name="Duração", value=f"{duration//3600} hora(s)", inline=True)
                embed.add_field(name="Apelação", value="Você pode solicitar uma apelação através do site do Sistema Guardião.", inline=False)
                await user.send(embed=embed)
            except:
                pass  # Usuário pode ter DMs desabilitadas
            
            # Aplicar ban
            await user.ban(reason=reason)
            print(f"🔨 Ban aplicado para {user.display_name}: {reason}")
            
            # TODO: Implementar sistema de unban automático após o tempo
            # Por enquanto, o ban é permanente até ser removido manualmente
            
            return True
        except Exception as e:
            print(f"❌ Erro ao aplicar ban: {e}")
            return False
    
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
    try:
        # Deferir resposta imediatamente para evitar timeout
        await interaction.response.defer(ephemeral=True)
        # Verificar se o usuário não está se reportando
        if usuario.id == interaction.user.id:
            await interaction.followup.send("❌ Você não pode se reportar!", ephemeral=True)
            return
        
        # SEMPRE buscar histórico completo do canal (até 100 mensagens das últimas 24h)
        print(f"🔍 Buscando histórico completo do canal {interaction.channel.id} (últimas 24h)...")
        recent_messages = []
        
        try:
            # Buscar últimas 100 mensagens do canal diretamente
            async for message in interaction.channel.history(limit=100):
                # Filtrar apenas mensagens das últimas 24 horas
                message_age = datetime.now() - message.created_at.replace(tzinfo=None)
                if message_age.total_seconds() <= 86400:  # 24 horas = 86400 segundos
                    recent_messages.append(message)
                else:
                    # Se a mensagem é mais antiga que 24h, parar de buscar
                    break
            print(f"✅ Coletadas {len(recent_messages)} mensagens das últimas 24h do canal")
        except Exception as e:
            print(f"❌ Erro ao buscar mensagens do canal: {e}")
            # Fallback: tentar usar cache se houver erro
            recent_messages = bot.message_cache.get_recent_messages(interaction.channel.id, 100)
            print(f"🔄 Fallback: usando {len(recent_messages)} mensagens do cache")
        
        # Criar denúncia no banco de dados
        from asgiref.sync import sync_to_async
        
        report = await sync_to_async(Report.objects.create)(
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            reported_user_id=usuario.id,
            reporter_user_id=interaction.user.id,
            reason=motivo,
            status='pending'
        )
        
        # Adicionar à fila de denúncias
        await sync_to_async(ReportQueue.objects.create)(
            report=report,
            status='pending',
            priority=1  # Prioridade padrão
        )
        
        # Log da criação da denúncia
        log_report_created(report.id, interaction.user.id, usuario.id, interaction.guild.id)
        
        # Anonimizar e salvar mensagens
        print(f"🔍 Salvando {len(recent_messages)} mensagens para denúncia #{report.id}")
        user_mapping = {}
        user_counter = 1
        
        for msg in recent_messages:
            if msg.author.id not in user_mapping:
                if msg.author.id == usuario.id:
                    user_mapping[msg.author.id] = "Usuário Denunciado"
                else:
                    # Todos os outros usuários (incluindo denunciante) são anonimizados
                    user_mapping[msg.author.id] = f"Usuário {user_counter}"
                    user_counter += 1
            
            # Coletar informações de mídias/anexos
            attachments_info = []
            has_attachments = False
            
            if msg.attachments:
                has_attachments = True
                for attachment in msg.attachments:
                    attachment_info = {
                        'filename': attachment.filename,
                        'url': attachment.url,
                        'size': attachment.size,
                        'content_type': attachment.content_type,
                        'is_image': attachment.content_type and attachment.content_type.startswith('image/'),
                        'is_video': attachment.content_type and attachment.content_type.startswith('video/'),
                    }
                    attachments_info.append(attachment_info)
            
            # Coletar emojis customizados (usando regex para encontrar emojis no conteúdo)
            import re
            emoji_pattern = r'<a?:\w+:\d+>'
            custom_emojis = re.findall(emoji_pattern, msg.content)
            if custom_emojis:
                has_attachments = True
                for emoji_match in custom_emojis:
                    emoji_info = {
                        'match': emoji_match,
                        'type': 'custom_emoji'
                    }
                    attachments_info.append(emoji_info)
            
            # Coletar stickers (se disponível)
            if hasattr(msg, 'stickers') and msg.stickers:
                has_attachments = True
                for sticker in msg.stickers:
                    sticker_info = {
                        'name': sticker.name,
                        'url': str(sticker.url) if sticker.url else None,
                        'type': 'sticker'
                    }
                    attachments_info.append(sticker_info)
            
            await sync_to_async(Message.objects.create)(
                report=report,
                original_user_id=msg.author.id,
                original_message_id=msg.id,
                anonymized_username=user_mapping[msg.author.id],
                content=msg.content,
                has_attachments=has_attachments,
                attachments_info=attachments_info if attachments_info else None,
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
        
        old_status = guardian.status
        guardian.last_activity = datetime.now()
        guardian.save()
        
        # Log da mudança de status
        log_guardian_status_change(guardian.id, old_status, guardian.status)
        
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


@bot.tree.command(name="info", description="Mostra informações sobre o Sistema Guardião")
async def info_command(interaction: discord.Interaction):
    """Comando para mostrar informações sobre o sistema"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Estatísticas do sistema
        from asgiref.sync import sync_to_async
        
        total_reports = await sync_to_async(Report.objects.count)()
        total_guardians = await sync_to_async(Guardian.objects.count)()
        online_guardians = await sync_to_async(Guardian.objects.filter(status='online').count)()
        pending_reports = await sync_to_async(Report.objects.filter(status='pending').count)()
        
        embed = discord.Embed(
            title="🛡️ Sistema Guardião",
            description="Uma plataforma completa de moderação para servidores Discord",
            color=0x58A6FF,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Estatísticas",
            value=f"**Denúncias:** {total_reports}\n**Guardiões:** {total_guardians}\n**Online:** {online_guardians}\n**Pendentes:** {pending_reports}",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Comandos",
            value="`/report` - Reportar usuário\n`/status` - Alterar status\n`/info` - Informações\n`/help` - Ajuda",
            inline=True
        )
        
        embed.add_field(
            name="🌐 Links",
            value=f"[Site]({bot.site_url})\n[Suporte]({bot.site_url}/support)\n[Documentação]({bot.site_url}/docs)",
            inline=True
        )
        
        embed.set_footer(text="Sistema Guardião - Mantendo servidores seguros")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"❌ Erro no comando info: {e}")
        await interaction.followup.send("❌ Ocorreu um erro ao obter informações.", ephemeral=True)


@bot.tree.command(name="help", description="Mostra ajuda sobre como usar o Sistema Guardião")
async def help_command(interaction: discord.Interaction):
    """Comando de ajuda"""
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="❓ Ajuda - Sistema Guardião",
        description="Como usar o sistema de moderação",
        color=0x39D353,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="🚨 Para Reportar",
        value="Use `/report @usuário motivo` para reportar violações das regras.\nO sistema coletará automaticamente o contexto da conversa.",
        inline=False
    )
    
    embed.add_field(
        name="👮 Para Guardiões",
        value="• `/status online` - Entrar em serviço\n• `/status offline` - Sair de serviço\n• Acesse o site para analisar denúncias",
        inline=False
    )
    
    embed.add_field(
        name="⚖️ Sistema de Votação",
        value="**Improcedente:** Não viola regras\n**Intimidou:** Violação leve\n**Grave:** Violação grave",
        inline=False
    )
    
    embed.add_field(
        name="🔗 Links Úteis",
        value=f"[Dashboard]({bot.site_url}/dashboard)\n[Lista de Denúncias]({bot.site_url}/reports/)\n[Painel Admin]({bot.site_url}/admin/)",
        inline=False
    )
    
    embed.set_footer(text="Para mais informações, visite nosso site")
    
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="sync", description="Sincroniza comandos slash (apenas para administradores)")
async def sync_command(interaction: discord.Interaction):
    """Comando para sincronizar comandos slash"""
    # Verificar se é administrador
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        synced = await bot.tree.sync()
        await interaction.followup.send(f"✅ {len(synced)} comandos sincronizados com sucesso!", ephemeral=True)
        log_system_event("COMMANDS_MANUAL_SYNC", f"{len(synced)} comandos sincronizados manualmente por {interaction.user.name}")
    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao sincronizar comandos: {str(e)}", ephemeral=True)
        log_error(f"Erro na sincronização manual: {e}")


@bot.tree.command(name="ping", description="Testa a latência do bot")
async def ping_command(interaction: discord.Interaction):
    """Comando de ping para testar latência"""
    await interaction.response.defer(ephemeral=True)
    
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: {latency}ms",
        color=0x39D353 if latency < 100 else 0xff6b6b,
        timestamp=datetime.now()
    )
    
    await interaction.followup.send(embed=embed, ephemeral=True)


async def main():
    """Função principal para executar o bot"""
    # Configurar logging
    logger = setup_logging()
    
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN não encontrado nas variáveis de ambiente!")
        log_error("DISCORD_BOT_TOKEN não encontrado nas variáveis de ambiente")
        return
    
    try:
        # Carregar comandos de administração
        from bot.admin_commands import setup as setup_admin_commands
        await setup_admin_commands(bot)
        
        # Iniciar servidor API
        from bot.api_server import start_api_server
        await start_api_server(bot)
        
        print("🤖 Iniciando Sistema Guardião Bot...")
        log_system_event("BOT_INITIALIZING", "Iniciando bot...")
        await bot.start(token)
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")
        log_error(f"Erro ao iniciar bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
