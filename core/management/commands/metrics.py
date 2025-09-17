"""
Comando Django para gerar relatório de métricas
"""
from django.core.management.base import BaseCommand
from core.metrics import metrics_command
import json


class Command(BaseCommand):
    """Comando para gerar relatório de métricas"""
    
    help = 'Gera relatório completo de métricas do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Arquivo de saída para o relatório (JSON)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'summary'],
            default='summary',
            help='Formato do relatório'
        )
    
    def handle(self, *args, **options):
        """Executa o comando de métricas"""
        try:
            report = metrics_command.generate_report()
            
            if not report:
                self.stdout.write(
                    self.style.ERROR('Erro ao gerar relatório de métricas')
                )
                return
            
            if options['format'] == 'json':
                self.output_json(report, options.get('output'))
            else:
                self.output_summary(report)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro: {e}')
            )
    
    def output_json(self, report, output_file):
        """Saída em formato JSON"""
        json_output = json.dumps(report, indent=2, ensure_ascii=False)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
            self.stdout.write(
                self.style.SUCCESS(f'Relatório salvo em: {output_file}')
            )
        else:
            self.stdout.write(json_output)
    
    def output_summary(self, report):
        """Saída em formato resumido"""
        overview = report['system_overview']
        guardian_stats = report['guardian_stats']
        health_score = report['health_score']
        
        self.stdout.write("=" * 60)
        self.stdout.write("📊 RELATÓRIO DE MÉTRICAS - SISTEMA GUARDIÃO")
        self.stdout.write("=" * 60)
        
        # Visão geral
        self.stdout.write("\n🔍 VISÃO GERAL DO SISTEMA")
        self.stdout.write("-" * 30)
        self.stdout.write(f"Total de Guardiões: {overview.get('total_guardians', 0)}")
        self.stdout.write(f"Guardiões Online: {overview.get('online_guardians', 0)}")
        self.stdout.write(f"Total de Denúncias: {overview.get('total_reports', 0)}")
        self.stdout.write(f"Denúncias Pendentes: {overview.get('pending_reports', 0)}")
        self.stdout.write(f"Denúncias em Votação: {overview.get('voting_reports', 0)}")
        self.stdout.write(f"Denúncias Concluídas: {overview.get('completed_reports', 0)}")
        
        # Estatísticas dos Guardiões
        self.stdout.write("\n👮 ESTATÍSTICAS DOS GUARDIÕES")
        self.stdout.write("-" * 30)
        self.stdout.write(f"Pontos Médios: {guardian_stats.get('average_points', 0):.1f}")
        self.stdout.write(f"Horas de Serviço Médias: {guardian_stats.get('average_service_hours', 0):.1f}")
        self.stdout.write(f"Precisão Geral: {guardian_stats.get('overall_accuracy', 0):.1f}%")
        
        # Distribuição por nível
        self.stdout.write("\n📈 DISTRIBUIÇÃO POR NÍVEL")
        self.stdout.write("-" * 30)
        for level in range(1, 6):
            count = guardian_stats.get(f'level_{level}', 0)
            self.stdout.write(f"Nível {level}: {count} Guardiões")
        
        # Score de saúde
        self.stdout.write("\n🏥 SCORE DE SAÚDE DO SISTEMA")
        self.stdout.write("-" * 30)
        self.stdout.write(f"Score: {health_score.get('score', 0)}/{health_score.get('max_score', 100)}")
        self.stdout.write(f"Percentual: {health_score.get('percentage', 0):.1f}%")
        self.stdout.write(f"Status: {health_score.get('status', 'unknown').upper()}")
        
        # Top Guardiões
        self.stdout.write("\n🏆 TOP 5 GUARDIÕES")
        self.stdout.write("-" * 30)
        top_guardians = report['top_guardians'][:5]
        for i, guardian in enumerate(top_guardians, 1):
            self.stdout.write(f"{i}. {guardian['discord_display_name']} - {guardian['points']} pontos (Nível {guardian['level']})")
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS('Relatório de métricas gerado com sucesso!')
        )
