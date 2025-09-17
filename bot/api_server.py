"""
Servidor HTTP para o Bot Discord receber comandos da API Django
"""
import asyncio
import json
import os
from aiohttp import web, ClientSession
from datetime import datetime
import discord
from discord.ext import commands
from bot.logging_config import log_system_event, log_error


class BotAPIServer:
    """Servidor HTTP para comunicação com Django"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Configura as rotas da API"""
        self.app.router.add_post('/apply_punishment/', self.apply_punishment_handler)
        self.app.router.add_post('/notify_guardians/', self.notify_guardians_handler)
        self.app.router.add_get('/health/', self.health_check_handler)
        self.app.router.add_get('/stats/', self.stats_handler)
    
    async def apply_punishment_handler(self, request):
        """Handler para aplicar punições"""
        try:
            data = await request.json()
            
            report_id = data.get('report_id')
            punishment = data.get('punishment')
            user_id = data.get('user_id')
            guild_id = data.get('guild_id')
            
            if not all([report_id, punishment, user_id, guild_id]):
                return web.json_response(
                    {'error': 'Dados obrigatórios ausentes'},
                    status=400
                )
            
            # Aplicar punição usando o bot
            success = await self.bot.apply_punishment_from_api(
                report_id, punishment, user_id, guild_id
            )
            
            if success:
                log_system_event("PUNISHMENT_APPLIED", f"Report {report_id}, User {user_id}")
                return web.json_response({'success': True})
            else:
                return web.json_response(
                    {'error': 'Falha ao aplicar punição'},
                    status=500
                )
                
        except Exception as e:
            log_error(f"Erro ao aplicar punição: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )
    
    async def notify_guardians_handler(self, request):
        """Handler para notificar Guardiões"""
        try:
            data = await request.json()
            
            report_id = data.get('report_id')
            guardian_ids = data.get('guardian_ids', [])
            
            if not report_id:
                return web.json_response(
                    {'error': 'report_id é obrigatório'},
                    status=400
                )
            
            # Notificar Guardiões
            await self.bot.notify_guardians_from_api(report_id, guardian_ids)
            
            log_system_event("GUARDIANS_NOTIFIED", f"Report {report_id}, {len(guardian_ids)} guardians")
            return web.json_response({'success': True})
            
        except Exception as e:
            log_error(f"Erro ao notificar Guardiões: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )
    
    async def health_check_handler(self, request):
        """Handler para verificação de saúde"""
        return web.json_response({
            'status': 'healthy',
            'bot_ready': self.bot.is_ready(),
            'guilds': len(self.bot.guilds),
            'timestamp': datetime.now().isoformat()
        })
    
    async def stats_handler(self, request):
        """Handler para estatísticas do bot"""
        try:
            stats = {
                'bot_ready': self.bot.is_ready(),
                'guilds_count': len(self.bot.guilds),
                'users_count': len(self.bot.users),
                'uptime': str(datetime.now() - self.bot.start_time) if hasattr(self.bot, 'start_time') else 'N/A',
                'commands_count': len(self.bot.tree.get_commands()),
            }
            
            return web.json_response({'success': True, 'stats': stats})
            
        except Exception as e:
            log_error(f"Erro ao obter estatísticas: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )
    
    async def start_server(self, host='0.0.0.0', port=8081):
        """Inicia o servidor HTTP"""
        import socket
        
        # Tentar encontrar uma porta disponível
        for attempt in range(5):
            try_port = port + attempt
            try:
                # Testar se a porta está disponível
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, try_port))
                sock.close()
                
                if result != 0:  # Porta disponível
                    runner = web.AppRunner(self.app)
                    await runner.setup()
                    site = web.TCPSite(runner, host, try_port)
                    await site.start()
                    
                    log_system_event("API_SERVER_STARTED", f"Servidor iniciado em {host}:{try_port}")
                    print(f"🌐 Servidor API do bot iniciado em {host}:{try_port}")
                    return
                    
            except Exception as e:
                if attempt == 4:  # Última tentativa
                    log_error(f"Erro ao iniciar servidor API após {attempt + 1} tentativas: {e}")
                    raise
                continue
        
        # Se chegou aqui, todas as tentativas falharam
        log_error("Não foi possível encontrar uma porta disponível para o servidor API")
        raise Exception("Não foi possível iniciar o servidor API")


# Adicionar métodos ao bot principal
async def add_api_methods_to_bot(bot):
    """Adiciona métodos de API ao bot"""
    
    async def apply_punishment_from_api(self, report_id, punishment, user_id, guild_id):
        """Aplica punição recebida via API"""
        try:
            guild = self.get_guild(guild_id)
            if not guild:
                return False
            
            user = guild.get_member(user_id)
            if not user:
                return False
            
            success = False
            
            if punishment == 'mute_1h':
                success = await self._apply_mute(user, 3600, f"Denúncia #{report_id} - Mute de 1 hora")
            elif punishment == 'mute_12h':
                success = await self._apply_mute(user, 43200, f"Denúncia #{report_id} - Mute de 12 horas")
            elif punishment == 'ban_24h':
                success = await self._apply_temp_ban(user, 86400, f"Denúncia #{report_id} - Banimento de 24 horas")
            
            return success
            
        except Exception as e:
            log_error(f"Erro ao aplicar punição via API: {e}")
            return False
    
    async def notify_guardians_from_api(self, report_id, guardian_ids):
        """Notifica Guardiões recebido via API"""
        try:
            for guardian_id in guardian_ids:
                try:
                    user = await self.fetch_user(guardian_id)
                    if user:
                        embed = discord.Embed(
                            title="🚨 Nova Denúncia Recebida",
                            description=f"Uma nova denúncia foi reportada e precisa de análise.",
                            color=0xff6b6b,
                            timestamp=datetime.now()
                        )
                        
                        embed.add_field(
                            name=f"Denúncia #{report_id}",
                            value="Clique no link abaixo para analisar",
                            inline=False
                        )
                        
                        site_url = os.getenv('SITE_URL', 'http://localhost:8080')
                        embed.add_field(
                            name="Link para Análise",
                            value=f"[Clique aqui para analisar]({site_url}/report/{report_id}/)",
                            inline=False
                        )
                        
                        await user.send(embed=embed)
                except Exception as e:
                    log_error(f"Erro ao notificar Guardião {guardian_id}: {e}")
                    
        except Exception as e:
            log_error(f"Erro ao notificar Guardiões via API: {e}")
    
    # Adicionar métodos ao bot
    bot.apply_punishment_from_api = apply_punishment_from_api.__get__(bot, type(bot))
    bot.notify_guardians_from_api = notify_guardians_from_api.__get__(bot, type(bot))
    
    return bot


async def start_api_server(bot):
    """Inicia o servidor API do bot"""
    bot = await add_api_methods_to_bot(bot)
    api_server = BotAPIServer(bot)
    
    # Iniciar servidor em uma task separada
    asyncio.create_task(api_server.start_server())
    
    return api_server
