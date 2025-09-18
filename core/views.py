"""
Views para o Sistema Guardião
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
import requests
import json
from .models import Guardian, Report, Vote, Message, Appeal
from .forms import VoteForm
from .decorators import guardian_required


def home(request):
    """Página inicial do sistema"""
    context = {
        'total_reports': Report.objects.count(),
        'total_guardians': Guardian.objects.count(),
        'online_guardians': Guardian.objects.filter(status='online').count(),
        'pending_reports': Report.objects.filter(status='pending').count(),
    }
    return render(request, 'core/home.html', context)


def discord_login(request):
    """Inicia o processo de login com Discord OAuth2"""
    from django.conf import settings
    
    client_id = settings.DISCORD_CLIENT_ID
    redirect_uri = f"{settings.SITE_URL}/auth/discord/callback/"
    
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=identify"
    )
    
    return redirect(discord_auth_url)


def discord_callback(request):
    """Callback do Discord OAuth2"""
    from django.conf import settings
    
    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Erro na autenticação com Discord')
        return redirect('home')
    
    try:
        # Trocar código por token
        token_data = {
            'client_id': settings.DISCORD_CLIENT_ID,
            'client_secret': settings.DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': f"{settings.SITE_URL}/auth/discord/callback/"
        }
        
        response = requests.post('https://discord.com/api/oauth2/token', data=token_data)
        token_response = response.json()
        
        if 'access_token' not in token_response:
            messages.error(request, 'Erro ao obter token do Discord')
            return redirect('home')
        
        # Obter informações do usuário
        headers = {'Authorization': f"Bearer {token_response['access_token']}"}
        user_response = requests.get('https://discord.com/api/users/@me', headers=headers)
        user_data = user_response.json()
        
        # Criar ou atualizar perfil do Guardião
        guardian, created = Guardian.objects.get_or_create(
            discord_id=user_data['id'],
            defaults={
                'discord_username': user_data['username'],
                'discord_display_name': user_data.get('display_name') or user_data['username'],
                'avatar_url': f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png" if user_data.get('avatar') else None,
                'status': 'offline',  # Começar como offline
                'level': 1,
                'points': 0,
            }
        )
        
        if not created:
            # Atualizar informações
            guardian.discord_username = user_data['username']
            guardian.discord_display_name = user_data.get('display_name') or user_data['username']
            guardian.avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png" if user_data.get('avatar') else None
            guardian.save()
            print(f"✅ Guardião existente atualizado: {guardian.discord_display_name} (ID: {guardian.discord_id})")
        else:
            print(f"🆕 Novo Guardião criado: {guardian.discord_display_name} (ID: {guardian.discord_id})")
        
        # Criar sessão de usuário
        request.session['guardian_id'] = guardian.discord_id  # Usar discord_id para API
        request.session['guardian_db_id'] = guardian.id  # ID do banco para outras operações
        
        messages.success(request, f'Bem-vindo, {guardian.discord_display_name}!')
        print(f"🔐 Sessão criada para Guardião: {guardian.discord_display_name} (discord_id: {guardian.discord_id})")
        return redirect('dashboard')
        
    except Exception as e:
        messages.error(request, f'Erro na autenticação: {str(e)}')
        return redirect('home')


def dashboard(request):
    """Dashboard do Guardião"""
    guardian_discord_id = request.session.get('guardian_id')
    
    if not guardian_discord_id:
        messages.error(request, 'Você precisa fazer login para acessar esta página.')
        return redirect('discord_login')
    
    try:
        guardian = Guardian.objects.get(discord_id=guardian_discord_id)
    except Guardian.DoesNotExist:
        messages.error(request, 'Perfil de Guardião não encontrado. Faça login novamente.')
        request.session.flush()
        return redirect('discord_login')
    
    # Denúncias pendentes
    pending_reports = Report.objects.filter(status='pending').order_by('-created_at')[:10]
    
    # Denúncias em votação onde o Guardião ainda não votou
    voting_reports = Report.objects.filter(
        status='voting'
    ).exclude(
        votes__guardian=guardian
    ).order_by('-created_at')[:10]
    
    context = {
        'guardian': guardian,
        'pending_reports': pending_reports,
        'voting_reports': voting_reports,
    }
    
    return render(request, 'core/dashboard.html', context)


def report_detail(request, report_id):
    """Página de análise de denúncia"""
    guardian_discord_id = request.session.get('guardian_id')
    
    if not guardian_discord_id:
        messages.error(request, 'Você precisa fazer login para acessar esta página.')
        return redirect('discord_login')
    
    try:
        guardian = Guardian.objects.get(discord_id=guardian_discord_id)
    except Guardian.DoesNotExist:
        messages.error(request, 'Perfil de Guardião não encontrado. Faça login novamente.')
        request.session.flush()
        return redirect('discord_login')
    
    report = get_object_or_404(Report, id=report_id)
    
    # Verificar se o Guardião já votou nesta denúncia
    has_voted = Vote.objects.filter(report=report, guardian=guardian).exists()
    
    # Obter mensagens da denúncia
    messages_list = Message.objects.filter(report=report).order_by('timestamp')
    
    # Obter votos existentes (sem mostrar quem votou)
    votes = Vote.objects.filter(report=report)
    
    context = {
        'guardian': guardian,
        'report': report,
        'messages': messages_list,
        'has_voted': has_voted,
        'votes': votes,
        'vote_form': VoteForm(),
    }
    
    return render(request, 'core/report_detail.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class VoteView(View):
    """View para processar votos"""
    
    def post(self, request, report_id):
        guardian_discord_id = request.session.get('guardian_id')
        if not guardian_discord_id:
            return JsonResponse({'error': 'Não autenticado'}, status=401)
        
        try:
            guardian = Guardian.objects.get(discord_id=guardian_discord_id)
        except Guardian.DoesNotExist:
            return JsonResponse({'error': 'Perfil de Guardião não encontrado'}, status=404)
        report = get_object_or_404(Report, id=report_id)
        
        # Verificar se já votou
        if Vote.objects.filter(report=report, guardian=guardian).exists():
            return JsonResponse({'error': 'Você já votou nesta denúncia'}, status=400)
        
        try:
            data = json.loads(request.body)
            vote_type = data.get('vote_type')
            
            if vote_type not in ['improcedente', 'intimidou', 'grave']:
                return JsonResponse({'error': 'Tipo de voto inválido'}, status=400)
            
            # Criar voto
            Vote.objects.create(
                report=report,
                guardian=guardian,
                vote_type=vote_type
            )
            
            # Atualizar contadores
            if vote_type == 'improcedente':
                report.votes_improcedente += 1
            elif vote_type == 'intimidou':
                report.votes_intimidou += 1
            elif vote_type == 'grave':
                report.votes_grave += 1
            
            report.total_votes += 1
            report.status = 'voting'
            report.save()
            
            # Verificar se a denúncia foi concluída
            if report.total_votes >= 5:
                report.status = 'completed'
                report.punishment = report.calculate_punishment()
                report.save()
                
                # Aqui seria enviada uma requisição para o bot aplicar a punição
                # TODO: Implementar integração com bot
            
            return JsonResponse({'success': True, 'message': 'Voto registrado com sucesso'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StatusToggleView(View):
    """View para alternar status do Guardião"""
    
    def post(self, request):
        guardian_discord_id = request.session.get('guardian_id')
        if not guardian_discord_id:
            return JsonResponse({'error': 'Não autenticado'}, status=401)
        
        try:
            guardian = Guardian.objects.get(discord_id=guardian_discord_id)
        except Guardian.DoesNotExist:
            return JsonResponse({'error': 'Perfil de Guardião não encontrado'}, status=404)
        
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if new_status not in ['online', 'offline']:
                return JsonResponse({'error': 'Status inválido'}, status=400)
            
            guardian.status = new_status
            guardian.save()
            
            return JsonResponse({
                'success': True,
                'status': guardian.status,
                'status_display': guardian.get_status_display()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


def reports_list(request):
    """Lista de denúncias"""
    reports = Report.objects.all().order_by('-created_at')
    
    # Paginação
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'core/reports_list.html', context)


def logout(request):
    """Logout do usuário"""
    request.session.flush()
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('home')