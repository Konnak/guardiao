"""
Sistema de backup e recuperação para o Sistema Guardião
"""
import os
import json
import zipfile
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from .models import Guardian, Report, Vote, Message, Appeal, AppealVote
from bot.logging_config import log_system_event, log_error


class BackupManager:
    """Gerenciador de backup do sistema"""
    
    def __init__(self):
        self.backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Garante que o diretório de backup existe"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_full_backup(self):
        """Cria backup completo do sistema"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'guardiao_backup_{timestamp}.zip'
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup dos dados principais
                self._backup_guardians(zipf)
                self._backup_reports(zipf)
                self._backup_votes(zipf)
                self._backup_messages(zipf)
                self._backup_appeals(zipf)
                self._backup_appeal_votes(zipf)
                
                # Backup de configurações
                self._backup_settings(zipf)
                
                # Backup de logs
                self._backup_logs(zipf)
            
            log_system_event("BACKUP_CREATED", f"Backup created: {backup_filename}")
            return backup_path
            
        except Exception as e:
            log_error(f"Erro ao criar backup: {e}")
            return None
    
    def _backup_guardians(self, zipf):
        """Backup dos Guardiões"""
        guardians_data = []
        for guardian in Guardian.objects.all():
            guardians_data.append({
                'id': guardian.id,
                'discord_id': guardian.discord_id,
                'discord_username': guardian.discord_username,
                'discord_display_name': guardian.discord_display_name,
                'avatar_url': guardian.avatar_url,
                'status': guardian.status,
                'level': guardian.level,
                'points': guardian.points,
                'total_service_hours': guardian.total_service_hours,
                'correct_votes': guardian.correct_votes,
                'incorrect_votes': guardian.incorrect_votes,
                'created_at': guardian.created_at.isoformat(),
                'updated_at': guardian.updated_at.isoformat(),
                'last_activity': guardian.last_activity.isoformat(),
            })
        
        zipf.writestr('guardians.json', json.dumps(guardians_data, indent=2))
    
    def _backup_reports(self, zipf):
        """Backup das denúncias"""
        reports_data = []
        for report in Report.objects.all():
            reports_data.append({
                'id': report.id,
                'guild_id': report.guild_id,
                'channel_id': report.channel_id,
                'reported_user_id': report.reported_user_id,
                'reporter_user_id': report.reporter_user_id,
                'reason': report.reason,
                'status': report.status,
                'punishment': report.punishment,
                'votes_improcedente': report.votes_improcedente,
                'votes_intimidou': report.votes_intimidou,
                'votes_grave': report.votes_grave,
                'total_votes': report.total_votes,
                'created_at': report.created_at.isoformat(),
                'completed_at': report.completed_at.isoformat() if report.completed_at else None,
            })
        
        zipf.writestr('reports.json', json.dumps(reports_data, indent=2))
    
    def _backup_votes(self, zipf):
        """Backup dos votos"""
        votes_data = []
        for vote in Vote.objects.all():
            votes_data.append({
                'id': vote.id,
                'report_id': vote.report_id,
                'guardian_id': vote.guardian_id,
                'vote_type': vote.vote_type,
                'created_at': vote.created_at.isoformat(),
            })
        
        zipf.writestr('votes.json', json.dumps(votes_data, indent=2))
    
    def _backup_messages(self, zipf):
        """Backup das mensagens"""
        messages_data = []
        for message in Message.objects.all():
            messages_data.append({
                'id': message.id,
                'report_id': message.report_id,
                'original_user_id': message.original_user_id,
                'original_message_id': message.original_message_id,
                'anonymized_username': message.anonymized_username,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'is_reported_user': message.is_reported_user,
                'created_at': message.created_at.isoformat(),
            })
        
        zipf.writestr('messages.json', json.dumps(messages_data, indent=2))
    
    def _backup_appeals(self, zipf):
        """Backup das apelações"""
        appeals_data = []
        for appeal in Appeal.objects.all():
            appeals_data.append({
                'id': appeal.id,
                'report_id': appeal.report_id,
                'appellant_user_id': appeal.appellant_user_id,
                'reason': appeal.reason,
                'status': appeal.status,
                'appeal_votes_improcedente': appeal.appeal_votes_improcedente,
                'appeal_votes_intimidou': appeal.appeal_votes_intimidou,
                'appeal_votes_grave': appeal.appeal_votes_grave,
                'appeal_total_votes': appeal.appeal_total_votes,
                'created_at': appeal.created_at.isoformat(),
                'completed_at': appeal.completed_at.isoformat() if appeal.completed_at else None,
            })
        
        zipf.writestr('appeals.json', json.dumps(appeals_data, indent=2))
    
    def _backup_appeal_votes(self, zipf):
        """Backup dos votos de apelação"""
        appeal_votes_data = []
        for appeal_vote in AppealVote.objects.all():
            appeal_votes_data.append({
                'id': appeal_vote.id,
                'appeal_id': appeal_vote.appeal_id,
                'guardian_id': appeal_vote.guardian_id,
                'vote_type': appeal_vote.vote_type,
                'created_at': appeal_vote.created_at.isoformat(),
            })
        
        zipf.writestr('appeal_votes.json', json.dumps(appeal_votes_data, indent=2))
    
    def _backup_settings(self, zipf):
        """Backup das configurações"""
        settings_data = {
            'SECRET_KEY': settings.SECRET_KEY,
            'DEBUG': settings.DEBUG,
            'ALLOWED_HOSTS': settings.ALLOWED_HOSTS,
            'DATABASE_NAME': settings.DATABASES['default']['NAME'],
            'LANGUAGE_CODE': settings.LANGUAGE_CODE,
            'TIME_ZONE': settings.TIME_ZONE,
        }
        
        zipf.writestr('settings.json', json.dumps(settings_data, indent=2))
    
    def _backup_logs(self, zipf):
        """Backup dos logs"""
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        if os.path.exists(logs_dir):
            for root, dirs, files in os.walk(logs_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, logs_dir)
                    zipf.write(file_path, f'logs/{arcname}')
    
    def restore_from_backup(self, backup_path):
        """Restaura sistema a partir de backup"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_path}")
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Limpar dados existentes
                self._clear_existing_data()
                
                # Restaurar dados
                self._restore_guardians(zipf)
                self._restore_reports(zipf)
                self._restore_votes(zipf)
                self._restore_messages(zipf)
                self._restore_appeals(zipf)
                self._restore_appeal_votes(zipf)
            
            log_system_event("BACKUP_RESTORED", f"Backup restored from: {backup_path}")
            return True
            
        except Exception as e:
            log_error(f"Erro ao restaurar backup: {e}")
            return False
    
    def _clear_existing_data(self):
        """Limpa dados existentes"""
        AppealVote.objects.all().delete()
        Appeal.objects.all().delete()
        Vote.objects.all().delete()
        Message.objects.all().delete()
        Report.objects.all().delete()
        Guardian.objects.all().delete()
    
    def _restore_guardians(self, zipf):
        """Restaura Guardiões"""
        guardians_data = json.loads(zipf.read('guardians.json'))
        
        for guardian_data in guardians_data:
            Guardian.objects.create(
                id=guardian_data['id'],
                discord_id=guardian_data['discord_id'],
                discord_username=guardian_data['discord_username'],
                discord_display_name=guardian_data['discord_display_name'],
                avatar_url=guardian_data['avatar_url'],
                status=guardian_data['status'],
                level=guardian_data['level'],
                points=guardian_data['points'],
                total_service_hours=guardian_data['total_service_hours'],
                correct_votes=guardian_data['correct_votes'],
                incorrect_votes=guardian_data['incorrect_votes'],
                created_at=datetime.fromisoformat(guardian_data['created_at']),
                updated_at=datetime.fromisoformat(guardian_data['updated_at']),
                last_activity=datetime.fromisoformat(guardian_data['last_activity']),
            )
    
    def _restore_reports(self, zipf):
        """Restaura denúncias"""
        reports_data = json.loads(zipf.read('reports.json'))
        
        for report_data in reports_data:
            Report.objects.create(
                id=report_data['id'],
                guild_id=report_data['guild_id'],
                channel_id=report_data['channel_id'],
                reported_user_id=report_data['reported_user_id'],
                reporter_user_id=report_data['reporter_user_id'],
                reason=report_data['reason'],
                status=report_data['status'],
                punishment=report_data['punishment'],
                votes_improcedente=report_data['votes_improcedente'],
                votes_intimidou=report_data['votes_intimidou'],
                votes_grave=report_data['votes_grave'],
                total_votes=report_data['total_votes'],
                created_at=datetime.fromisoformat(report_data['created_at']),
                completed_at=datetime.fromisoformat(report_data['completed_at']) if report_data['completed_at'] else None,
            )
    
    def _restore_votes(self, zipf):
        """Restaura votos"""
        votes_data = json.loads(zipf.read('votes.json'))
        
        for vote_data in votes_data:
            Vote.objects.create(
                id=vote_data['id'],
                report_id=vote_data['report_id'],
                guardian_id=vote_data['guardian_id'],
                vote_type=vote_data['vote_type'],
                created_at=datetime.fromisoformat(vote_data['created_at']),
            )
    
    def _restore_messages(self, zipf):
        """Restaura mensagens"""
        messages_data = json.loads(zipf.read('messages.json'))
        
        for message_data in messages_data:
            Message.objects.create(
                id=message_data['id'],
                report_id=message_data['report_id'],
                original_user_id=message_data['original_user_id'],
                original_message_id=message_data['original_message_id'],
                anonymized_username=message_data['anonymized_username'],
                content=message_data['content'],
                timestamp=datetime.fromisoformat(message_data['timestamp']),
                is_reported_user=message_data['is_reported_user'],
                created_at=datetime.fromisoformat(message_data['created_at']),
            )
    
    def _restore_appeals(self, zipf):
        """Restaura apelações"""
        appeals_data = json.loads(zipf.read('appeals.json'))
        
        for appeal_data in appeals_data:
            Appeal.objects.create(
                id=appeal_data['id'],
                report_id=appeal_data['report_id'],
                appellant_user_id=appeal_data['appellant_user_id'],
                reason=appeal_data['reason'],
                status=appeal_data['status'],
                appeal_votes_improcedente=appeal_data['appeal_votes_improcedente'],
                appeal_votes_intimidou=appeal_data['appeal_votes_intimidou'],
                appeal_votes_grave=appeal_data['appeal_votes_grave'],
                appeal_total_votes=appeal_data['appeal_total_votes'],
                created_at=datetime.fromisoformat(appeal_data['created_at']),
                completed_at=datetime.fromisoformat(appeal_data['completed_at']) if appeal_data['completed_at'] else None,
            )
    
    def _restore_appeal_votes(self, zipf):
        """Restaura votos de apelação"""
        appeal_votes_data = json.loads(zipf.read('appeal_votes.json'))
        
        for appeal_vote_data in appeal_votes_data:
            AppealVote.objects.create(
                id=appeal_vote_data['id'],
                appeal_id=appeal_vote_data['appeal_id'],
                guardian_id=appeal_vote_data['guardian_id'],
                vote_type=appeal_vote_data['vote_type'],
                created_at=datetime.fromisoformat(appeal_vote_data['created_at']),
            )
    
    def cleanup_old_backups(self, days_to_keep=30):
        """Remove backups antigos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('guardiao_backup_') and filename.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        log_system_event("OLD_BACKUP_REMOVED", f"Removed: {filename}")
            
        except Exception as e:
            log_error(f"Erro ao limpar backups antigos: {e}")


class BackupCommand(BaseCommand):
    """Comando Django para criar backup"""
    
    help = 'Cria backup completo do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--restore',
            type=str,
            help='Caminho para arquivo de backup para restaurar'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Remove backups antigos'
        )
    
    def handle(self, *args, **options):
        """Executa o comando de backup"""
        backup_manager = BackupManager()
        
        if options['restore']:
            self.restore_backup(backup_manager, options['restore'])
        elif options['cleanup']:
            self.cleanup_backups(backup_manager)
        else:
            self.create_backup(backup_manager)
    
    def create_backup(self, backup_manager):
        """Cria novo backup"""
        self.stdout.write('Criando backup do sistema...')
        
        backup_path = backup_manager.create_full_backup()
        
        if backup_path:
            self.stdout.write(
                self.style.SUCCESS(f'Backup criado com sucesso: {backup_path}')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Erro ao criar backup')
            )
    
    def restore_backup(self, backup_manager, backup_path):
        """Restaura backup"""
        self.stdout.write(f'Restaurando backup de: {backup_path}')
        
        if backup_manager.restore_from_backup(backup_path):
            self.stdout.write(
                self.style.SUCCESS('Backup restaurado com sucesso')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Erro ao restaurar backup')
            )
    
    def cleanup_backups(self, backup_manager):
        """Limpa backups antigos"""
        self.stdout.write('Removendo backups antigos...')
        
        backup_manager.cleanup_old_backups()
        
        self.stdout.write(
            self.style.SUCCESS('Limpeza de backups concluída')
        )
