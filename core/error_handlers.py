"""
Handlers de erro customizados para o Sistema Guardião
"""
import logging
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Handler customizado para exceções da API
    """
    # Obter resposta padrão do DRF
    response = exception_handler(exc, context)
    
    if response is not None:
        # Personalizar resposta de erro
        custom_response_data = {
            'error': True,
            'message': 'Ocorreu um erro interno do servidor',
            'timestamp': timezone.now().isoformat(),
            'details': str(exc) if settings.DEBUG else 'Detalhes não disponíveis em produção'
        }
        
        # Adicionar informações específicas baseadas no tipo de erro
        if isinstance(exc, ValidationError):
            custom_response_data['message'] = 'Dados de entrada inválidos'
            custom_response_data['validation_errors'] = exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
        
        response.data = custom_response_data
        
        # Log do erro
        logger.error(f"API Error: {exc}", exc_info=True, extra={
            'request_path': context.get('request').path if context.get('request') else 'Unknown',
            'request_method': context.get('request').method if context.get('request') else 'Unknown',
            'user_id': getattr(context.get('request').user, 'id', None) if context.get('request') and hasattr(context.get('request'), 'user') else None,
        })
    
    return response


def handle_guardian_not_found(guardian_id):
    """
    Handler específico para quando um Guardião não é encontrado
    """
    logger.warning(f"Guardião não encontrado: discord_id={guardian_id}")
    
    return Response({
        'error': True,
        'message': f'Guardião com ID {guardian_id} não encontrado',
        'timestamp': timezone.now().isoformat(),
        'suggestion': 'Verifique se o ID do Discord está correto ou se o usuário está registrado no sistema'
    }, status=status.HTTP_404_NOT_FOUND)


def handle_report_not_found(report_id):
    """
    Handler específico para quando uma denúncia não é encontrada
    """
    logger.warning(f"Denúncia não encontrada: report_id={report_id}")
    
    return Response({
        'error': True,
        'message': f'Denúncia #{report_id} não encontrada',
        'timestamp': timezone.now().isoformat(),
        'suggestion': 'Verifique se o ID da denúncia está correto'
    }, status=status.HTTP_404_NOT_FOUND)


def handle_voting_session_error(session_id, error_message):
    """
    Handler específico para erros em sessões de votação
    """
    logger.error(f"Erro em sessão de votação: session_id={session_id}, error={error_message}")
    
    return Response({
        'error': True,
        'message': 'Erro na sessão de votação',
        'timestamp': timezone.now().isoformat(),
        'details': error_message,
        'session_id': session_id
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_database_error(operation, error):
    """
    Handler para erros de banco de dados
    """
    logger.error(f"Erro de banco de dados na operação '{operation}': {error}", exc_info=True)
    
    return Response({
        'error': True,
        'message': 'Erro interno do banco de dados',
        'timestamp': timezone.now().isoformat(),
        'operation': operation,
        'details': str(error) if settings.DEBUG else 'Detalhes não disponíveis em produção'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_validation_error(field, value, error_message):
    """
    Handler para erros de validação
    """
    logger.warning(f"Erro de validação: field={field}, value={value}, error={error_message}")
    
    return Response({
        'error': True,
        'message': 'Dados de entrada inválidos',
        'timestamp': timezone.now().isoformat(),
        'validation_errors': {
            field: [error_message]
        }
    }, status=status.HTTP_400_BAD_REQUEST)


def log_api_request(request, response_data, guardian_id=None):
    """
    Log de requisições da API para auditoria
    """
    log_data = {
        'method': request.method,
        'path': request.path,
        'query_params': dict(request.GET),
        'response_status': response_data.get('success', False),
        'guardian_id': guardian_id,
        'timestamp': timezone.now().isoformat(),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        'ip_address': request.META.get('REMOTE_ADDR', 'Unknown')
    }
    
    if response_data.get('success'):
        logger.info(f"API Request Success: {log_data}")
    else:
        logger.warning(f"API Request Error: {log_data}")


def create_error_response(message, details=None, status_code=500):
    """
    Cria uma resposta de erro padronizada
    """
    error_response = {
        'error': True,
        'message': message,
        'timestamp': timezone.now().isoformat()
    }
    
    if details:
        error_response['details'] = details
    
    return Response(error_response, status=status_code)
