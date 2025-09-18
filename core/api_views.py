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
from .models import Guardian, Report, Vote, Message, Appeal, VotingSession, SessionGuardian, ReportQueue
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
@csrf_exempt
def update_guardian_status(request):
    """
    Endpoint para atualizar status do Guardião
    """
    try:
        print("✅ API NOVA CHAMADA: /api/guardians/status/")
        
        data = request.data
        new_status = data.get('status')
        print(f"🔄 Status solicitado: {new_status}")
        
        if not new_status:
            print("❌ Status é obrigatório")
            return Response(
                {'error': 'status é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in ['online', 'offline']:
            print("❌ Status inválido")
            return Response(
                {'error': 'Status inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obter discord_id da sessão
        guardian_discord_id = request.session.get('guardian_id')
        print(f"🔍 Discord ID da sessão: {guardian_discord_id}")
        
        if not guardian_discord_id:
            print("❌ Usuário não logado")
            return Response(
                {'error': 'Usuário não logado'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            guardian = Guardian.objects.get(discord_id=guardian_discord_id)
            print(f"✅ Guardião encontrado: {guardian.discord_display_name} (ID: {guardian.discord_id})")
        except Guardian.DoesNotExist:
            print("❌ Guardião não encontrado")
            return Response(
                {'error': 'Guardião não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        old_status = guardian.status
        guardian.status = new_status
        guardian.save()
        print(f"✅ Status alterado de {old_status} para {new_status}")
        print(f"🔍 Verificando status após save: {guardian.status}")
        
        status_display = 'Em Serviço' if new_status == 'online' else 'Fora de Serviço'
        
        return Response({
            'success': True,
            'message': f'Status alterado de {old_status} para {new_status}',
            'status': new_status,
            'status_display': status_display,
            'guardian': GuardianSerializer(guardian).data
        })
        
    except Exception as e:
        print(f"❌ Erro: {e}")
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
def check_session(request):
    """
    Endpoint para verificar se o usuário está logado
    """
    try:
        # Verificar se há sessão ativa
        guardian_id = request.session.get('guardian_id')
        guardian_db_id = request.session.get('guardian_db_id')
        
        print(f"🔍 check_session - guardian_id: {guardian_id}, guardian_db_id: {guardian_db_id}")
        
        if guardian_id and guardian_db_id:
            print(f"✅ Sessão válida - retornando guardian_id: {guardian_id}")
            response_data = {
                'authenticated': True,
                'guardian_id': str(guardian_id),  # CORREÇÃO: Converter para string
                'guardian_db_id': guardian_db_id
            }
            print(f"🔍 Dados sendo retornados: {response_data}")
            return Response(response_data)
        else:
            print(f"❌ Sessão inválida - guardian_id: {guardian_id}, guardian_db_id: {guardian_db_id}")
            return Response({
                'authenticated': False,
                'message': 'Usuário não logado'
            })
            
    except Exception as e:
        return Response(
            {'authenticated': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def check_new_reports(request):
    """
    Endpoint para verificar novas denúncias (para notificações em tempo real)
    """
    try:
        from datetime import datetime
        
        # Obter timestamp da última verificação
        last_check = request.GET.get('last_check')
        
        if last_check:
            try:
                from django.utils import timezone
                # Converter para timezone-aware datetime
                last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                if last_check_dt.tzinfo is None:
                    last_check_dt = timezone.make_aware(last_check_dt)
                
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
        
        from django.utils import timezone
        
        return Response({
            'success': True,
            'new_reports': reports_data,
            'count': len(reports_data),
            'timestamp': timezone.now().isoformat()
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


# ===== NOVOS ENDPOINTS PARA SISTEMA DE FILA E MODAL =====

@api_view(['GET'])
@permission_classes([AllowAny])
def get_pending_report_for_guardian(request, guardian_id):
    """
    Endpoint para obter a próxima denúncia pendente para um Guardião
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Verificar se o Guardião está online
        try:
            guardian = Guardian.objects.get(discord_id=guardian_id, status='online')
            print(f"✅ Guardião encontrado: {guardian.discord_display_name} (ID: {guardian.discord_id}, Status: {guardian.status})")
        except Guardian.DoesNotExist:
            # Verificar se o Guardião existe mas está offline
            try:
                guardian_offline = Guardian.objects.get(discord_id=guardian_id)
                print(f"❌ Guardião encontrado mas offline: {guardian_offline.discord_display_name} (ID: {guardian_offline.discord_id}, Status: {guardian_offline.status})")
                return Response({'error': f'Guardião {guardian_offline.discord_display_name} está offline. Entre em serviço primeiro.'}, status=status.HTTP_404_NOT_FOUND)
            except Guardian.DoesNotExist:
                print(f"❌ Guardião com discord_id {guardian_id} não encontrado no banco")
                
                # Criar Guardião automaticamente se for um ID válido
                print(f"❌ Guardião com discord_id {guardian_id} não encontrado - tentando criar automaticamente")
                
                # Verificar se é um discord_id válido (maior que 1000000000000000)
                if int(guardian_id) > 1000000000000000:
                    try:
                        # Criar Guardião usando get_or_create para evitar duplicação
                        guardian, created = Guardian.objects.get_or_create(
                            discord_id=guardian_id,
                            defaults={
                                'discord_username': f"User{guardian_id}",
                                'discord_display_name': f"Usuário {guardian_id}",
                                'status': 'online',  # Criar como online por padrão
                                'level': 1,
                                'points': 0
                            }
                        )
                        
                        if created:
                            print(f"🆕 Guardião criado automaticamente: {guardian.discord_display_name} (ID: {guardian.discord_id})")
                        else:
                            print(f"✅ Guardião encontrado após criação: {guardian.discord_display_name} (ID: {guardian.discord_id})")
                    except Exception as e:
                        print(f"❌ Erro ao criar Guardião: {e}")
                        return Response({'error': f'Erro ao criar Guardião: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return Response({'error': f'Guardião com ID {guardian_id} não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se já está em uma sessão ativa SEM TER VOTADO
        active_session = SessionGuardian.objects.filter(
            guardian=guardian,
            is_active=True,
            has_voted=False
        ).first()
        
        if active_session:
            # Verificar se a sessão ainda está válida (não expirou)
            if active_session.session.voting_deadline and active_session.session.voting_deadline < timezone.now():
                # Sessão expirada - marcar como inativa e continuar
                active_session.is_active = False
                active_session.left_at = timezone.now()
                active_session.save()
                print(f"⏰ Sessão expirada para guardião {guardian.discord_display_name}")
            else:
                # Retornar a sessão atual válida
                session_data = {
                    'session_id': str(active_session.session.id),
                    'report_id': active_session.session.report.id,
                    'report': {
                        'id': active_session.session.report.id,
                        'reason': active_session.session.report.reason,
                        'reported_user_id': active_session.session.report.reported_user_id,
                        'reporter_user_id': active_session.session.report.reporter_user_id,
                        'created_at': active_session.session.report.created_at.isoformat(),
                    },
                    'messages': [],
                    'voting_deadline': active_session.session.voting_deadline.isoformat() if active_session.session.voting_deadline else None,
                    'time_remaining': None
                }
                
                # Calcular tempo restante
                if active_session.session.voting_deadline:
                    remaining = active_session.session.voting_deadline - timezone.now()
                    session_data['time_remaining'] = max(0, int(remaining.total_seconds()))
                
                # Buscar mensagens da denúncia
                messages = Message.objects.filter(report=active_session.session.report).order_by('timestamp')
                session_data['messages'] = [
                    {
                        'id': msg.id,
                        'original_user_id': msg.original_user_id,
                        'anonymized_username': msg.anonymized_username,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat(),
                        'is_reported_user': msg.is_reported_user
                    }
                    for msg in messages
                ]
                
                return Response(session_data)
        
        # Buscar próxima denúncia na fila que o guardião ainda não votou
        queue_items = ReportQueue.objects.filter(
            status__in=['pending', 'assigned']
        ).order_by('-priority', 'created_at')
        
        print(f"🔍 Buscando denúncia na fila para guardião {guardian.discord_display_name}")
        print(f"🔍 Total de itens na fila: {queue_items.count()}")
        
        queue_item = None
        for item in queue_items:
            # Verificar se o guardião já votou nesta denúncia
            has_voted = Vote.objects.filter(
                report=item.report,
                guardian=guardian
            ).exists()
            
            if not has_voted:
                queue_item = item
                print(f"✅ Denúncia encontrada: {item} (Guardião ainda não votou)")
                break
            else:
                print(f"⏭️ Pulando denúncia {item.report.id} (Guardião já votou)")
        
        if not queue_item:
            # Verificar se há denúncias sem fila
            reports_without_queue = Report.objects.filter(
                status='pending'
            ).exclude(
                reportqueue__isnull=False
            ).order_by('-created_at')
            
            print(f"🔍 Denúncias sem fila: {reports_without_queue.count()}")
            
            if reports_without_queue.exists():
                # Criar fila para denúncias órfãs
                for report in reports_without_queue:
                    ReportQueue.objects.get_or_create(
                        report=report,
                        defaults={'status': 'pending', 'priority': 0}
                    )
                    print(f"✅ Fila criada para denúncia #{report.id}")
                
                # Buscar novamente
                queue_item = ReportQueue.objects.filter(
                    status__in=['pending', 'assigned']
                ).order_by('-priority', 'created_at').first()
            
            if not queue_item:
                return Response({'message': 'Nenhuma denúncia pendente na fila'})
        
        # Verificar se já existe sessão ativa para esta denúncia
        existing_session = VotingSession.objects.filter(
            report=queue_item.report,
            status__in=['waiting', 'voting']
        ).first()
        
        if existing_session:
            # Verificar se o guardião já votou nesta denúncia
            existing_vote = Vote.objects.filter(
                report=queue_item.report,
                guardian=guardian
            ).exists()
            
            if existing_vote:
                return Response({
                    'error': 'Você já votou nesta denúncia anteriormente',
                    'message': 'Não é possível participar novamente desta denúncia'
                })
            
            # Adicionar guardião à sessão existente
            session_guardian, created = SessionGuardian.objects.get_or_create(
                session=existing_session,
                guardian=guardian,
                defaults={'is_active': True}
            )
            
            if not created:
                return Response({
                    'error': 'Você já está participando desta sessão',
                    'message': 'Aguarde sua vez de votar'
                })
            
            session = existing_session
        else:
            # Criar nova sessão de votação
            session = VotingSession.objects.create(
                report=queue_item.report,
                status='waiting',
                voting_deadline=timezone.now() + timedelta(minutes=5)
            )
            
            # Adicionar Guardião à sessão
            SessionGuardian.objects.create(
                session=session,
                guardian=guardian,
                is_active=True
            )
            
            # Atualizar status da fila
            queue_item.status = 'assigned'
            queue_item.assigned_at = timezone.now()
            queue_item.save()
            
            # Atualizar status da sessão
            session.status = 'voting'
            session.started_at = timezone.now()
            session.save()
        
        # Retornar dados da sessão
        session_data = {
            'session_id': str(session.id),
            'report_id': session.report.id,
            'report': {
                'id': session.report.id,
                'reason': session.report.reason,
                'reported_user_id': session.report.reported_user_id,
                'reporter_user_id': session.report.reporter_user_id,
                'created_at': session.report.created_at.isoformat(),
            },
            'messages': [],
            'voting_deadline': session.voting_deadline.isoformat(),
            'time_remaining': 300  # 5 minutos em segundos
        }
        
        # Buscar mensagens da denúncia
        messages = Message.objects.filter(report=session.report).order_by('timestamp')
        print(f"🔍 Mensagens encontradas para denúncia {session.report.id}: {messages.count()}")
        
        session_data['messages'] = [
            {
                'id': msg.id,
                'original_user_id': msg.original_user_id,
                'anonymized_username': msg.anonymized_username,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'is_reported_user': msg.is_reported_user
            }
            for msg in messages
        ]
        
        print(f"🔍 Mensagens retornadas: {len(session_data['messages'])}")
        
        return Response(session_data)
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao obter denúncia pendente: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_guardian_status(request, guardian_id):
    """
    Endpoint para verificar o status de um Guardião
    """
    try:
        print(f"🔍 Verificando status do Guardião ID: {guardian_id}")
        try:
            guardian = Guardian.objects.get(discord_id=guardian_id)
            print(f"✅ Guardião encontrado: {guardian.discord_display_name} (Status: {guardian.status})")
            return Response({
                'success': True,
                'guardian': {
                    'id': guardian.id,
                    'discord_id': guardian.discord_id,
                    'discord_display_name': guardian.discord_display_name,
                    'status': guardian.status,
                    'level': guardian.level,
                    'points': guardian.points
                },
                'is_online': guardian.status == 'online'
            })
        except Guardian.DoesNotExist:
            # Se for discord_id 1 (usuário de teste), criar um Guardião temporário
            if guardian_id == 1:
                print(f"🔧 Criando Guardião temporário para discord_id {guardian_id}")
                guardian = Guardian.objects.create(
                    discord_id=guardian_id,
                    discord_username="TestUser",
                    discord_display_name="Usuário de Teste",
                    status='online',  # Criar como online por padrão
                    level=1,
                    points=0
                )
                return Response({
                    'success': True,
                    'guardian': {
                        'id': guardian.id,
                        'discord_id': guardian.discord_id,
                        'discord_display_name': guardian.discord_display_name,
                        'status': guardian.status,
                        'level': guardian.level,
                        'points': guardian.points
                    },
                    'is_online': guardian.status == 'online'
                })
            else:
                # Para discord_ids reais, criar automaticamente se for um ID válido
                print(f"❌ Guardião com discord_id {guardian_id} não encontrado - tentando criar automaticamente")
                
                # Verificar se é um discord_id válido (maior que 1000000000000000)
                if int(guardian_id) > 1000000000000000:
                    try:
                        # Criar Guardião usando get_or_create para evitar duplicação
                        guardian, created = Guardian.objects.get_or_create(
                            discord_id=guardian_id,
                            defaults={
                                'discord_username': f"User{guardian_id}",
                                'discord_display_name': f"Usuário {guardian_id}",
                                'status': 'online',  # Criar como online por padrão
                                'level': 1,
                                'points': 0
                            }
                        )
                        
                        if created:
                            print(f"🆕 Guardião criado automaticamente: {guardian.discord_display_name} (ID: {guardian.discord_id})")
                        else:
                            print(f"✅ Guardião encontrado após criação: {guardian.discord_display_name} (ID: {guardian.discord_id})")
                        
                        return Response({
                            'success': True,
                            'guardian': {
                                'id': guardian.id,
                                'discord_id': guardian.discord_id,
                                'discord_display_name': guardian.discord_display_name,
                                'status': guardian.status,
                                'level': guardian.level,
                                'points': guardian.points
                            },
                            'is_online': guardian.status == 'online',
                            'message': 'Guardião criado automaticamente' if created else 'Guardião encontrado'
                        })
                    except Exception as e:
                        print(f"❌ Erro ao criar Guardião: {e}")
                        return Response({
                            'success': False,
                            'error': f'Erro ao criar perfil de Guardião',
                            'message': 'Tente fazer login no site primeiro',
                            'discord_id': guardian_id
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return Response({
                        'success': False,
                        'error': f'Usuário não registrado como Guardião',
                        'message': 'Para se tornar um Guardião, faça login no site primeiro',
                        'discord_id': guardian_id
                    }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response(
            {'error': f'Erro ao verificar status do Guardião: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def cast_vote_in_session(request):
    """
    Endpoint para registrar voto em uma sessão de votação
    """
    try:
        from django.utils import timezone
        
        data = request.data
        
        # Validar dados
        required_fields = ['session_id', 'guardian_id', 'vote_type']
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
        
        # Buscar sessão e Guardião
        try:
            print(f"🔍 cast_vote_in_session - Dados recebidos: {data}")
            print(f"🔍 cast_vote_in_session - session_id: {data.get('session_id')}")
            print(f"🔍 cast_vote_in_session - guardian_id: {data.get('guardian_id')}")
            print(f"🔍 cast_vote_in_session - vote_type: {data.get('vote_type')}")
            
            session = VotingSession.objects.get(id=data['session_id'])
            guardian = Guardian.objects.get(discord_id=data['guardian_id'])
            session_guardian = SessionGuardian.objects.get(
                session=session,
                guardian=guardian,
                is_active=True
            )
        except (VotingSession.DoesNotExist, Guardian.DoesNotExist, SessionGuardian.DoesNotExist):
            return Response(
                {'error': 'Sessão ou Guardião não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar se já votou
        if session_guardian.has_voted:
            return Response(
                {'error': 'Você já votou nesta sessão'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se a sessão expirou
        if session.is_expired():
            return Response(
                {'error': 'Tempo de votação expirado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Registrar voto
        session_guardian.has_voted = True
        session_guardian.vote_type = data['vote_type']
        session_guardian.voted_at = timezone.now()
        session_guardian.save()
        
        # Criar voto permanente (sempre criar novo, não usar get_or_create)
        vote, created = Vote.objects.get_or_create(
            report=session.report,
            guardian=guardian,
            defaults={'vote_type': data['vote_type']}
        )
        
        # Se já existe voto, não permitir votar novamente
        if not created:
            return Response(
                {'error': 'Você já votou nesta denúncia anteriormente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Atualizar contadores da denúncia
        report = session.report
        if data['vote_type'] == 'improcedente':
            report.votes_improcedente += 1
        elif data['vote_type'] == 'intimidou':
            report.votes_intimidou += 1
        elif data['vote_type'] == 'grave':
            report.votes_grave += 1
        
        report.total_votes += 1
        report.status = 'voting'
        report.save()
        
        # Verificar se todos os Guardiões ativos votaram
        active_guardians = session.get_active_guardians()
        voted_guardians = active_guardians.filter(has_voted=True)
        
        if voted_guardians.count() >= 5:
            # Concluir sessão
            session.status = 'completed'
            session.completed_at = timezone.now()
            session.save()
            
            # Concluir denúncia
            report.status = 'completed'
            report.punishment = report.calculate_punishment()
            report.save()
            
            # Atualizar fila
            try:
                queue_item = ReportQueue.objects.get(report=report)
                queue_item.status = 'completed'
                queue_item.completed_at = timezone.now()
                queue_item.save()
            except ReportQueue.DoesNotExist:
                print(f"⚠️ Item da fila não encontrado para denúncia {report.id}")
            
            # Notificar bot para aplicar punição
            # notify_bot_apply_punishment(report) # Desabilitado por enquanto
        
        # Buscar votos anônimos para mostrar
        anonymous_votes = []
        all_votes = Vote.objects.filter(report=session.report).order_by('created_at')
        for vote in all_votes:
            anonymous_votes.append({
                'vote_type': vote.vote_type,
                'vote_display': vote.get_vote_type_display(),
                'timestamp': vote.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'message': 'Voto registrado com sucesso',
            'vote_type': data['vote_type'],  # Adicionar vote_type na resposta
            'session_completed': session.status == 'completed',
            'votes_count': voted_guardians.count(),
            'total_active_guardians': active_guardians.count(),
            'anonymous_votes': anonymous_votes,
            'total_votes': all_votes.count()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao registrar voto: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def leave_voting_session(request):
    """
    Endpoint para Guardião sair de uma sessão de votação
    """
    try:
        from django.utils import timezone
        
        data = request.data
        
        # Validar dados
        if 'session_id' not in data or 'guardian_id' not in data:
            return Response(
                {'error': 'Campos obrigatórios ausentes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar sessão e Guardião
        try:
            print(f"🔍 leave_voting_session - Dados recebidos: {data}")
            print(f"🔍 leave_voting_session - session_id: {data.get('session_id')}")
            print(f"🔍 leave_voting_session - guardian_id: {data.get('guardian_id')}")
            
            session = VotingSession.objects.get(id=data['session_id'])
            guardian = Guardian.objects.get(discord_id=data['guardian_id'])
            session_guardian = SessionGuardian.objects.get(
                session=session,
                guardian=guardian,
                is_active=True
            )
            print(f"🔍 leave_voting_session - Sessão encontrada: {session.id}")
            print(f"🔍 leave_voting_session - Guardião encontrado: {guardian.discord_display_name}")
            print(f"🔍 leave_voting_session - SessionGuardian encontrado: {session_guardian.id}")
        except (VotingSession.DoesNotExist, Guardian.DoesNotExist, SessionGuardian.DoesNotExist) as e:
            print(f"❌ leave_voting_session - Erro ao buscar: {e}")
            return Response(
                {'error': 'Sessão ou Guardião não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Marcar como inativo
        session_guardian.is_active = False
        session_guardian.left_at = timezone.now()
        session_guardian.save()
        
        # Se não votou, cancelar o voto
        if not session_guardian.has_voted:
            # Remover da sessão
            session_guardian.delete()
            
            # Verificar se ainda há Guardiões ativos
            active_guardians = session.get_active_guardians()
            if active_guardians.count() == 0:
                # Cancelar sessão e recolocar na fila
                session.status = 'cancelled'
                session.save()
                
                queue_item = ReportQueue.objects.get(report=session.report)
                queue_item.status = 'pending'
                queue_item.assigned_at = None
                queue_item.save()
        
        return Response({
            'success': True,
            'message': 'Saiu da sessão com sucesso'
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erro ao sair da sessão: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


