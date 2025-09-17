"""
Sistema de métricas e monitoramento para o Sistema Guardião
"""
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Guardian, Report, Vote, Appeal
from bot.logging_config import log_system_event, log_error


class MetricsCollector:
    """Coletor de métricas do sistema"""
    
    def get_system_overview(self):
        """Obtém visão geral do sistema"""
        try:
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            last_30d = now - timedelta(days=30)
            
            return {
                'total_guardians': Guardian.objects.count(),
                'online_guardians': Guardian.objects.filter(status='online').count(),
                'total_reports': Report.objects.count(),
                'pending_reports': Report.objects.filter(status='pending').count(),
                'voting_reports': Report.objects.filter(status='voting').count(),
                'completed_reports': Report.objects.filter(status='completed').count(),
                'total_votes': Vote.objects.count(),
                'total_appeals': Appeal.objects.count(),
                
                # Métricas de tempo
                'reports_24h': Report.objects.filter(created_at__gte=last_24h).count(),
                'reports_7d': Report.objects.filter(created_at__gte=last_7d).count(),
                'reports_30d': Report.objects.filter(created_at__gte=last_30d).count(),
                
                'votes_24h': Vote.objects.filter(created_at__gte=last_24h).count(),
                'votes_7d': Vote.objects.filter(created_at__gte=last_7d).count(),
                'votes_30d': Vote.objects.filter(created_at__gte=last_30d).count(),
            }
            
        except Exception as e:
            log_error(f"Erro ao coletar métricas do sistema: {e}")
            return {}
    
    def get_guardian_stats(self):
        """Obtém estatísticas dos Guardiões"""
        try:
            guardians = Guardian.objects.all()
            
            if not guardians.exists():
                return {}
            
            total_points = sum(g.points for g in guardians)
            total_service_hours = sum(g.total_service_hours for g in guardians)
            total_correct_votes = sum(g.correct_votes for g in guardians)
            total_incorrect_votes = sum(g.incorrect_votes for g in guardians)
            
            return {
                'total_guardians': guardians.count(),
                'online_guardians': guardians.filter(status='online').count(),
                'offline_guardians': guardians.filter(status='offline').count(),
                
                # Distribuição por nível
                'level_1': guardians.filter(level=1).count(),
                'level_2': guardians.filter(level=2).count(),
                'level_3': guardians.filter(level=3).count(),
                'level_4': guardians.filter(level=4).count(),
                'level_5': guardians.filter(level=5).count(),
                
                # Estatísticas agregadas
                'total_points': total_points,
                'average_points': total_points / guardians.count() if guardians.count() > 0 else 0,
                'total_service_hours': total_service_hours,
                'average_service_hours': total_service_hours / guardians.count() if guardians.count() > 0 else 0,
                
                # Precisão de votação
                'total_correct_votes': total_correct_votes,
                'total_incorrect_votes': total_incorrect_votes,
                'overall_accuracy': (total_correct_votes / (total_correct_votes + total_incorrect_votes) * 100) if (total_correct_votes + total_incorrect_votes) > 0 else 0,
            }
            
        except Exception as e:
            log_error(f"Erro ao coletar estatísticas dos Guardiões: {e}")
            return {}
    
    def get_report_stats(self):
        """Obtém estatísticas das denúncias"""
        try:
            reports = Report.objects.all()
            
            if not reports.exists():
                return {}
            
            # Distribuição por status
            status_distribution = {}
            for status_choice in Report.STATUS_CHOICES:
                status_distribution[status_choice[0]] = reports.filter(status=status_choice[0]).count()
            
            # Distribuição por punição
            punishment_distribution = {}
            for punishment_choice in Report.PUNISHMENT_CHOICES:
                punishment_distribution[punishment_choice[0]] = reports.filter(punishment=punishment_choice[0]).count()
            
            # Distribuição de votos
            total_improcedente = sum(r.votes_improcedente for r in reports)
            total_intimidou = sum(r.votes_intimidou for r in reports)
            total_grave = sum(r.votes_grave for r in reports)
            
            return {
                'total_reports': reports.count(),
                'status_distribution': status_distribution,
                'punishment_distribution': punishment_distribution,
                
                # Estatísticas de votação
                'total_improcedente_votes': total_improcedente,
                'total_intimidou_votes': total_intimidou,
                'total_grave_votes': total_grave,
                'total_votes': total_improcedente + total_intimidou + total_grave,
                
                # Percentuais de votação
                'improcedente_percentage': (total_improcedente / (total_improcedente + total_intimidou + total_grave) * 100) if (total_improcedente + total_intimidou + total_grave) > 0 else 0,
                'intimidou_percentage': (total_intimidou / (total_improcedente + total_intimidou + total_grave) * 100) if (total_improcedente + total_intimidou + total_grave) > 0 else 0,
                'grave_percentage': (total_grave / (total_improcedente + total_intimidou + total_grave) * 100) if (total_improcedente + total_intimidou + total_grave) > 0 else 0,
            }
            
        except Exception as e:
            log_error(f"Erro ao coletar estatísticas das denúncias: {e}")
            return {}
    
    def get_performance_metrics(self):
        """Obtém métricas de performance"""
        try:
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # Tempo médio de processamento de denúncias
            completed_reports = Report.objects.filter(
                status='completed',
                completed_at__isnull=False
            )
            
            processing_times = []
            for report in completed_reports:
                if report.completed_at and report.created_at:
                    processing_time = (report.completed_at - report.created_at).total_seconds() / 3600  # em horas
                    processing_times.append(processing_time)
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Taxa de conclusão
            total_reports_24h = Report.objects.filter(created_at__gte=last_24h).count()
            completed_reports_24h = Report.objects.filter(
                created_at__gte=last_24h,
                status='completed'
            ).count()
            
            completion_rate_24h = (completed_reports_24h / total_reports_24h * 100) if total_reports_24h > 0 else 0
            
            # Atividade dos Guardiões
            active_guardians_24h = Guardian.objects.filter(
                last_activity__gte=last_24h
            ).count()
            
            active_guardians_7d = Guardian.objects.filter(
                last_activity__gte=last_7d
            ).count()
            
            return {
                'average_processing_time_hours': round(avg_processing_time, 2),
                'completion_rate_24h': round(completion_rate_24h, 2),
                'active_guardians_24h': active_guardians_24h,
                'active_guardians_7d': active_guardians_7d,
                'total_processing_times': len(processing_times),
            }
            
        except Exception as e:
            log_error(f"Erro ao coletar métricas de performance: {e}")
            return {}
    
    def get_trend_data(self, days=30):
        """Obtém dados de tendência"""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Dados diários
            daily_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                daily_reports = Report.objects.filter(
                    created_at__gte=current_date,
                    created_at__lt=next_date
                ).count()
                
                daily_votes = Vote.objects.filter(
                    created_at__gte=current_date,
                    created_at__lt=next_date
                ).count()
                
                daily_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'reports': daily_reports,
                    'votes': daily_votes,
                })
                
                current_date = next_date
            
            return {
                'period_days': days,
                'daily_data': daily_data,
                'total_reports_period': sum(d['reports'] for d in daily_data),
                'total_votes_period': sum(d['votes'] for d in daily_data),
            }
            
        except Exception as e:
            log_error(f"Erro ao coletar dados de tendência: {e}")
            return {}
    
    def get_top_guardians(self, limit=10):
        """Obtém top Guardiões por pontos"""
        try:
            top_guardians = Guardian.objects.order_by('-points', '-level')[:limit]
            
            return [
                {
                    'id': guardian.id,
                    'discord_display_name': guardian.discord_display_name,
                    'level': guardian.level,
                    'points': guardian.points,
                    'correct_votes': guardian.correct_votes,
                    'incorrect_votes': guardian.incorrect_votes,
                    'accuracy_percentage': guardian.accuracy_percentage,
                    'total_service_hours': guardian.total_service_hours,
                    'status': guardian.status,
                }
                for guardian in top_guardians
            ]
            
        except Exception as e:
            log_error(f"Erro ao obter top Guardiões: {e}")
            return []
    
    def get_system_health_score(self):
        """Calcula score de saúde do sistema"""
        try:
            overview = self.get_system_overview()
            guardian_stats = self.get_guardian_stats()
            performance = self.get_performance_metrics()
            
            score = 0
            max_score = 100
            
            # Score baseado em Guardiões online (30 pontos)
            if overview.get('total_guardians', 0) > 0:
                online_ratio = overview.get('online_guardians', 0) / overview.get('total_guardians', 1)
                score += min(30, online_ratio * 30)
            
            # Score baseado em taxa de conclusão (25 pontos)
            completion_rate = performance.get('completion_rate_24h', 0)
            score += min(25, completion_rate * 0.25)
            
            # Score baseado em precisão geral (25 pontos)
            accuracy = guardian_stats.get('overall_accuracy', 0)
            score += min(25, accuracy * 0.25)
            
            # Score baseado em tempo de processamento (20 pontos)
            avg_time = performance.get('average_processing_time_hours', 0)
            if avg_time > 0:
                # Menor tempo = maior score (máximo 24 horas = 0 pontos)
                time_score = max(0, 20 - (avg_time / 24 * 20))
                score += time_score
            
            return {
                'score': round(score, 2),
                'max_score': max_score,
                'percentage': round((score / max_score) * 100, 2),
                'status': self._get_health_status(score / max_score),
            }
            
        except Exception as e:
            log_error(f"Erro ao calcular score de saúde: {e}")
            return {'score': 0, 'max_score': 100, 'percentage': 0, 'status': 'unknown'}
    
    def _get_health_status(self, score_ratio):
        """Determina status de saúde baseado no score"""
        if score_ratio >= 0.8:
            return 'excellent'
        elif score_ratio >= 0.6:
            return 'good'
        elif score_ratio >= 0.4:
            return 'fair'
        elif score_ratio >= 0.2:
            return 'poor'
        else:
            return 'critical'


class MetricsCommand:
    """Comando para gerar relatório de métricas"""
    
    def __init__(self):
        self.collector = MetricsCollector()
    
    def generate_report(self):
        """Gera relatório completo de métricas"""
        try:
            report = {
                'timestamp': timezone.now().isoformat(),
                'system_overview': self.collector.get_system_overview(),
                'guardian_stats': self.collector.get_guardian_stats(),
                'report_stats': self.collector.get_report_stats(),
                'performance_metrics': self.collector.get_performance_metrics(),
                'health_score': self.collector.get_system_health_score(),
                'top_guardians': self.collector.get_top_guardians(),
                'trend_data_7d': self.collector.get_trend_data(7),
                'trend_data_30d': self.collector.get_trend_data(30),
            }
            
            log_system_event("METRICS_REPORT_GENERATED", "Full metrics report generated")
            return report
            
        except Exception as e:
            log_error(f"Erro ao gerar relatório de métricas: {e}")
            return None


# Instância global
metrics_collector = MetricsCollector()
metrics_command = MetricsCommand()
