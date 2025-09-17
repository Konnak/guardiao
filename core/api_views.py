"""
API Views para o Sistema Guardião
Integração entre Django e Bot Discord
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
import json
import requests
import os
from .models import Guardian, Report, Vote, Message, Appeal
from .serializers import ReportSerializer, VoteSerializer, GuardianSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def create_report(request):
    """
    Endpoint para o bot criar uma nova denúncia
    """
    try:
        data = request.data
        
        # Validar dados obrigatórios
        required_fields = ['guild_id', 'channel_id', 'reported_user_id', 'reporter_user_id']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'Campo obrigatório ausente: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Criar denúncia
        report = Report.objects.create(
            guild_id=data['guild_id'],
            channel_id=data['channel_id'],
            reported_user_id=data['reported_user_id'],
            reporter_user_id=data['reporter_user_id'],
            reason=data.get('reason', ''),
            status='pending'
        )
        
        # Criar mensagens se fornecidas
        if 'messages' in data:
            for msg_data in data['messages']:
                Message.objects.create(
                    report=report,
                    original_user_id=msg_data['original_user_id'],
                    original_message_id=msg_data['original_message_id'],
                    anonymized_username=msg_data['anonymized_username'],
                    content=msg_data['content'],
                    timestamp=msg_data['timestamp'],
                    is_reported_user=msg_data.get('is_reported_user', False)
                )
        
        # Notificar Guardiões online
        notify_guardians(report)
        
        return Response({
            'success': True,
            'report_id': report.id,
            'message': 'Denúncia criada com sucesso'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao criar denúncia: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def apply_punishment(request):
    """
    Endpoint para o bot aplicar punições
    """
    try:
        data = request.data
        report_id = data.get('report_id')
        
        if not report_id:
            return Response(
                {'error': 'report_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response(
                {'error': 'Denúncia não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Enviar comando para o bot aplicar punição
        bot_url = os.getenv('BOT_API_URL', 'http://localhost:8081')
        bot_response = requests.post(f'{bot_url}/apply_punishment/', json={
            'report_id': report_id,
            'punishment': report.punishment,
            'user_id': report.reported_user_id,
            'guild_id': report.guild_id
        })
        
        if bot_response.status_code == 200:
            return Response({
                'success': True,
                'message': 'Punição aplicada com sucesso'
            })
        else:
            return Response(
                {'error': 'Erro ao aplicar punição no bot'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao processar punição: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_online_guardians(request):
    """
    Endpoint para obter lista de Guardiões online
    """
    try:
        guardians = Guardian.objects.filter(status='online')
        serializer = GuardianSerializer(guardians, many=True)
        
        return Response({
            'success': True,
            'guardians': serializer.data,
            'count': guardians.count()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao obter Guardiões: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def cast_vote(request):
    """
    Endpoint para registrar um voto
    """
    try:
        data = request.data
        
        # Validar dados
        required_fields = ['report_id', 'guardian_id', 'vote_type']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'Campo obrigatório ausente: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Verificar se o voto é válido
        if data['vote_type'] not in ['improcedente', 'intimidou', 'grave']:
            return Response(
                {'error': 'Tipo de voto inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se a denúncia existe
        try:
            report = Report.objects.get(id=data['report_id'])
        except Report.DoesNotExist:
            return Response(
                {'error': 'Denúncia não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar se o Guardião existe
        try:
            guardian = Guardian.objects.get(id=data['guardian_id'])
        except Guardian.DoesNotExist:
            return Response(
                {'error': 'Guardião não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar se já votou
        if Vote.objects.filter(report=report, guardian=guardian).exists():
            return Response(
                {'error': 'Guardião já votou nesta denúncia'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Criar voto
        vote = Vote.objects.create(
            report=report,
            guardian=guardian,
            vote_type=data['vote_type']
        )
        
        # Atualizar contadores
        if data['vote_type'] == 'improcedente':
            report.votes_improcedente += 1
        elif data['vote_type'] == 'intimidou':
            report.votes_intimidou += 1
        elif data['vote_type'] == 'grave':
            report.votes_grave += 1
        
        report.total_votes += 1
        report.status = 'voting'
        report.save()
        
        # Verificar se a denúncia foi concluída
        if report.total_votes >= 5:
            report.status = 'completed'
            report.punishment = report.calculate_punishment()
            report.save()
            
            # Notificar bot para aplicar punição
            notify_bot_apply_punishment(report)
        
        return Response({
            'success': True,
            'vote_id': vote.id,
            'message': 'Voto registrado com sucesso',
            'report_completed': report.total_votes >= 5
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao registrar voto: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_report_details(request, report_id):
    """
    Endpoint para obter detalhes de uma denúncia
    """
    try:
        report = Report.objects.get(id=report_id)
        serializer = ReportSerializer(report)
        
        return Response({
            'success': True,
            'report': serializer.data
        })
        
    except Report.DoesNotExist:
        return Response(
            {'error': 'Denúncia não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erro ao obter denúncia: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def update_guardian_status(request):
    """
    Endpoint para atualizar status do Guardião
    """
    try:
        data = request.data
        guardian_id = data.get('guardian_id')
        new_status = data.get('status')
        
        if not guardian_id or not new_status:
            return Response(
                {'error': 'guardian_id e status são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in ['online', 'offline']:
            return Response(
                {'error': 'Status inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            guardian = Guardian.objects.get(id=guardian_id)
        except Guardian.DoesNotExist:
            return Response(
                {'error': 'Guardião não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        old_status = guardian.status
        guardian.status = new_status
        guardian.save()
        
        return Response({
            'success': True,
            'message': f'Status alterado de {old_status} para {new_status}',
            'guardian': GuardianSerializer(guardian).data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao atualizar status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_stats(request):
    """
    Endpoint para obter estatísticas do dashboard
    """
    try:
        stats = {
            'total_reports': Report.objects.count(),
            'total_guardians': Guardian.objects.count(),
            'online_guardians': Guardian.objects.filter(status='online').count(),
            'pending_reports': Report.objects.filter(status='pending').count(),
            'voting_reports': Report.objects.filter(status='voting').count(),
            'completed_reports': Report.objects.filter(status='completed').count(),
        }
        
        return Response({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao obter estatísticas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def check_new_reports(request):
    """
    Endpoint para verificar novas denúncias (para notificações em tempo real)
    """
    try:
        # Obter timestamp da última verificação
        last_check = request.GET.get('last_check')
        
        if last_check:
            from datetime import datetime
            try:
                last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                new_reports = Report.objects.filter(
                    created_at__gt=last_check_dt,
                    status='pending'
                ).order_by('-created_at')
            except ValueError:
                # Se timestamp inválido, retornar todas as denúncias pendentes
                new_reports = Report.objects.filter(status='pending').order_by('-created_at')
        else:
            # Primeira verificação - retornar todas as denúncias pendentes
            new_reports = Report.objects.filter(status='pending').order_by('-created_at')
        
        reports_data = []
        for report in new_reports:
            reports_data.append({
                'id': report.id,
                'reason': report.reason,
                'created_at': report.created_at.isoformat(),
                'reported_user_id': report.reported_user_id,
                'reporter_user_id': report.reporter_user_id,
                'guild_id': report.guild_id,
                'channel_id': report.channel_id,
            })
        
        return Response({
            'success': True,
            'new_reports': reports_data,
            'count': len(reports_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao verificar novas denúncias: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Funções auxiliares
def notify_guardians(report):
    """
    Notifica Guardiões online sobre nova denúncia
    """
    try:
        online_guardians = Guardian.objects.filter(status='online')
        
        # Aqui seria enviada uma notificação para o bot Discord
        # para que ele envie DMs para os Guardiões
        bot_url = os.getenv('BOT_API_URL', 'http://localhost:8081')
        requests.post(f'{bot_url}/notify_guardians/', json={
            'report_id': report.id,
            'guardian_ids': list(online_guardians.values_list('discord_id', flat=True))
        })
        
    except Exception as e:
        print(f"Erro ao notificar Guardiões: {e}")


def notify_bot_apply_punishment(report):
    """
    Notifica o bot para aplicar punição
    """
    try:
        bot_url = os.getenv('BOT_API_URL', 'http://localhost:8081')
        requests.post(f'{bot_url}/apply_punishment/', json={
            'report_id': report.id,
            'punishment': report.punishment,
            'user_id': report.reported_user_id,
            'guild_id': report.guild_id
        })
        
    except Exception as e:
        print(f"Erro ao notificar bot sobre punição: {e}")
