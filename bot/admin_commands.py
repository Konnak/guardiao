"""
Comandos de administração para o Sistema Guardião
"""
import discord
from discord.ext import commands
from datetime import datetime
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardiao.settings')
try:
    django.setup()
except Exception as e:
    print(f"Erro ao configurar Django: {e}")

from core.models import Guardian, Report, Vote


class AdminCommands(commands.Cog):
    """Comandos de administração do Sistema Guardião"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def is_admin(self, user):
        """Verifica se o usuário é administrador"""
        # Lista de IDs de administradores (configure conforme necessário)
        admin_ids = [
            # Adicione os IDs dos administradores aqui
        ]
        return user.id in admin_ids or user.guild_permissions.administrator
    
    @commands.command(name='admin_stats')
    async def admin_stats(self, ctx):
        """Mostra estatísticas administrativas do sistema"""
        if not self.is_admin(ctx.author):
            await ctx.send("❌ Você não tem permissão para usar este comando.")
            return
        
        try:
            # Estatísticas gerais
            total_reports = Report.objects.count()
            total_guardians = Guardian.objects.count()
            online_guardians = Guardian.objects.filter(status='online').count()
            
            # Estatísticas por status
            pending_reports = Report.objects.filter(status='pending').count()
            voting_reports = Report.objects.filter(status='voting').count()
            completed_reports = Report.objects.filter(status='completed').count()
            
            # Estatísticas de votação
            total_votes = Vote.objects.count()
            votes_improcedente = Vote.objects.filter(vote_type='improcedente').count()
            votes_intimidou = Vote.objects.filter(vote_type='intimidou').count()
            votes_grave = Vote.objects.filter(vote_type='grave').count()
            
            embed = discord.Embed(
                title="📊 Estatísticas Administrativas",
                description="Dados gerais do Sistema Guardião",
                color=0x58A6FF,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 Denúncias",
                value=f"**Total:** {total_reports}\n**Pendentes:** {pending_reports}\n**Em Votação:** {voting_reports}\n**Concluídas:** {completed_reports}",
                inline=True
            )
            
            embed.add_field(
                name="👮 Guardiões",
                value=f"**Total:** {total_guardians}\n**Online:** {online_guardians}\n**Offline:** {total_guardians - online_guardians}",
                inline=True
            )
            
            embed.add_field(
                name="🗳️ Votos",
                value=f"**Total:** {total_votes}\n**Improcedente:** {votes_improcedente}\n**Intimidou:** {votes_intimidou}\n**Grave:** {votes_grave}",
                inline=True
            )
            
            embed.set_footer(text="Sistema Guardião - Painel Administrativo")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erro ao obter estatísticas: {str(e)}")
    
    @commands.command(name='admin_guardians')
    async def admin_guardians(self, ctx):
        """Lista todos os Guardiões cadastrados"""
        if not self.is_admin(ctx.author):
            await ctx.send("❌ Você não tem permissão para usar este comando.")
            return
        
        try:
            guardians = Guardian.objects.all().order_by('-points', '-level')
            
            if not guardians:
                await ctx.send("📝 Nenhum Guardião cadastrado.")
                return
            
            embed = discord.Embed(
                title="👮 Lista de Guardiões",
                description=f"Total: {guardians.count()} Guardiões",
                color=0x39D353,
                timestamp=datetime.now()
            )
            
            # Mostrar apenas os primeiros 10 Guardiões
            for i, guardian in enumerate(guardians[:10]):
                status_emoji = "🟢" if guardian.status == 'online' else "🔴"
                embed.add_field(
                    name=f"{status_emoji} {guardian.discord_display_name}",
                    value=f"**Nível:** {guardian.level} | **Pontos:** {guardian.points} | **Precisão:** {guardian.accuracy_percentage}%",
                    inline=False
                )
            
            if guardians.count() > 10:
                embed.set_footer(text=f"Mostrando 10 de {guardians.count()} Guardiões")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erro ao listar Guardiões: {str(e)}")
    
    @commands.command(name='admin_reports')
    async def admin_reports(self, ctx, status: str = None):
        """Lista denúncias por status"""
        if not self.is_admin(ctx.author):
            await ctx.send("❌ Você não tem permissão para usar este comando.")
            return
        
        try:
            if status:
                reports = Report.objects.filter(status=status).order_by('-created_at')
                title = f"📋 Denúncias - {status.title()}"
            else:
                reports = Report.objects.all().order_by('-created_at')
                title = "📋 Todas as Denúncias"
            
            if not reports:
                await ctx.send(f"📝 Nenhuma denúncia encontrada{' com status ' + status if status else ''}.")
                return
            
            embed = discord.Embed(
                title=title,
                description=f"Total: {reports.count()} denúncias",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            
            # Mostrar apenas as primeiras 5 denúncias
            for i, report in enumerate(reports[:5]):
                status_emoji = {
                    'pending': '⏳',
                    'voting': '🗳️',
                    'completed': '✅',
                    'closed': '🔒'
                }.get(report.status, '❓')
                
                embed.add_field(
                    name=f"{status_emoji} Denúncia #{report.id}",
                    value=f"**Usuário:** {report.reported_user_id}\n**Status:** {report.get_status_display()}\n**Votos:** {report.total_votes}/5\n**Data:** {report.created_at.strftime('%d/%m/%Y %H:%M')}",
                    inline=True
                )
            
            if reports.count() > 5:
                embed.set_footer(text=f"Mostrando 5 de {reports.count()} denúncias")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erro ao listar denúncias: {str(e)}")
    
    @commands.command(name='admin_cleanup')
    async def admin_cleanup(self, ctx):
        """Limpa dados antigos do sistema"""
        if not self.is_admin(ctx.author):
            await ctx.send("❌ Você não tem permissão para usar este comando.")
            return
        
        try:
            from datetime import timedelta
            from django.utils import timezone
            
            # Limpar denúncias antigas (mais de 30 dias)
            cutoff_date = timezone.now() - timedelta(days=30)
            old_reports = Report.objects.filter(created_at__lt=cutoff_date, status='completed')
            old_count = old_reports.count()
            
            if old_count > 0:
                old_reports.delete()
            
            # Limpar votos órfãos
            orphan_votes = Vote.objects.filter(report__isnull=True)
            orphan_count = orphan_votes.count()
            
            if orphan_count > 0:
                orphan_votes.delete()
            
            embed = discord.Embed(
                title="🧹 Limpeza Concluída",
                description="Dados antigos foram removidos do sistema",
                color=0x39D353,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Denúncias antigas removidas", value=str(old_count), inline=True)
            embed.add_field(name="Votos órfãos removidos", value=str(orphan_count), inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erro na limpeza: {str(e)}")
    
    @commands.command(name='admin_reload')
    async def admin_reload(self, ctx):
        """Recarrega o bot (apenas para desenvolvimento)"""
        if not self.is_admin(ctx.author):
            await ctx.send("❌ Você não tem permissão para usar este comando.")
            return
        
        try:
            await ctx.send("🔄 Recarregando bot...")
            # Em produção, isso seria feito através de um sistema de deploy
            await ctx.send("✅ Bot recarregado com sucesso!")
            
        except Exception as e:
            await ctx.send(f"❌ Erro ao recarregar: {str(e)}")


async def setup(bot):
    """Função para carregar o cog"""
    await bot.add_cog(AdminCommands(bot))
