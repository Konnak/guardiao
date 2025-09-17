from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Guardian, Report, Vote, Message, Appeal, AppealVote


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = [
        'discord_display_name', 
        'discord_username', 
        'status', 
        'level', 
        'points', 
        'accuracy_percentage',
        'total_service_hours',
        'last_activity'
    ]
    list_filter = ['status', 'level', 'created_at']
    search_fields = ['discord_username', 'discord_display_name']
    readonly_fields = ['created_at', 'updated_at', 'last_activity']
    
    fieldsets = (
        ('Informações do Discord', {
            'fields': ('discord_id', 'discord_username', 'discord_display_name', 'avatar_url')
        }),
        ('Status e Nível', {
            'fields': ('status', 'level', 'points')
        }),
        ('Estatísticas', {
            'fields': ('total_service_hours', 'correct_votes', 'incorret_votes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'reported_user_id',
        'reporter_user_id',
        'status',
        'punishment',
        'total_votes',
        'votes_summary',
        'created_at'
    ]
    list_filter = ['status', 'punishment', 'created_at']
    search_fields = ['reported_user_id', 'reporter_user_id', 'reason']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Informações da Denúncia', {
            'fields': ('guild_id', 'channel_id', 'reported_user_id', 'reporter_user_id', 'reason')
        }),
        ('Status e Punição', {
            'fields': ('status', 'punishment')
        }),
        ('Contagem de Votos', {
            'fields': ('votes_improcedente', 'votes_intimidou', 'votes_grave', 'total_votes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def votes_summary(self, obj):
        """Exibe um resumo dos votos"""
        return f"Imp: {obj.votes_improcedente} | Int: {obj.votes_intimidou} | Grav: {obj.votes_grave}"
    votes_summary.short_description = "Resumo dos Votos"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['guardian', 'report', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['guardian__discord_display_name', 'report__id']
    readonly_fields = ['created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'report',
        'anonymized_username',
        'content_preview',
        'is_reported_user',
        'timestamp'
    ]
    list_filter = ['is_reported_user', 'timestamp', 'created_at']
    search_fields = ['anonymized_username', 'content']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        """Exibe uma prévia do conteúdo da mensagem"""
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content
    content_preview.short_description = "Prévia do Conteúdo"


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = [
        'report',
        'appellant_user_id',
        'status',
        'appeal_total_votes',
        'appeal_votes_summary',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['appellant_user_id', 'reason']
    readonly_fields = ['created_at', 'completed_at']
    
    def appeal_votes_summary(self, obj):
        """Exibe um resumo dos votos da apelação"""
        return f"Imp: {obj.appeal_votes_improcedente} | Int: {obj.appeal_votes_intimidou} | Grav: {obj.appeal_votes_grave}"
    appeal_votes_summary.short_description = "Resumo dos Votos (Apelação)"


@admin.register(AppealVote)
class AppealVoteAdmin(admin.ModelAdmin):
    list_display = ['guardian', 'appeal', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['guardian__discord_display_name', 'appeal__report__id']
    readonly_fields = ['created_at']


# Personalização do título do admin
admin.site.site_header = "Sistema Guardião - Administração"
admin.site.site_title = "Guardião Admin"
admin.site.index_title = "Painel de Administração"