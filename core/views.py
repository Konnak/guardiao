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
        
        # Buscar data de criação da conta Discord
        discord_account_created_at = None
        if 'id' in user_data:
            # Converter Discord ID para timestamp (Discord IDs contêm timestamp de criação)
            discord_id = int(user_data['id'])
            # Discord IDs são snowflakes que contêm timestamp
            # Os primeiros 22 bits são o timestamp (em milissegundos desde 2015-01-01)
            timestamp_ms = (discord_id >> 22) + 1420070400000  # 1420070400000 é o epoch do Discord
            discord_account_created_at = timezone.datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        
        # Criar ou atualizar perfil do Guardião
        guardian, created = Guardian.objects.get_or_create(
            discord_id=user_data['id'],
            defaults={
                'discord_username': user_data['username'],
                'discord_display_name': user_data.get('display_name') or user_data['username'],
                'avatar_url': f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png" if user_data.get('avatar') else None,
                'role': 'usuario',  # Sempre começar como USUARIO
                'discord_account_created_at': discord_account_created_at,
                'status': 'offline',  # Começar como offline
                'level': 1,
                'points': 0,
            }
        )
        
        if not created:
            # Atualizar informações (mas manter role se já for guardian)
            guardian.discord_username = user_data['username']
            guardian.discord_display_name = user_data.get('display_name') or user_data['username']
            guardian.avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png" if user_data.get('avatar') else None
            
            # Atualizar data de criação se não estiver definida
            if not guardian.discord_account_created_at and discord_account_created_at:
                guardian.discord_account_created_at = discord_account_created_at
            
            guardian.save()
            print(f"✅ Guardião existente atualizado: {guardian.discord_display_name} (ID: {guardian.discord_id}, Role: {guardian.role})")
        else:
            print(f"🆕 Novo Guardião criado: {guardian.discord_display_name} (ID: {guardian.discord_id}, Role: {guardian.role})")
        
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
    """Dashboard do Guardião/Usuário"""
    guardian_discord_id = request.session.get('guardian_id')
    
    if not guardian_discord_id:
        messages.error(request, 'Você precisa fazer login para acessar esta página.')
        return redirect('discord_login')
    
    try:
        guardian = Guardian.objects.get(discord_id=guardian_discord_id)
    except Guardian.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado. Faça login novamente.')
        request.session.flush()
        return redirect('discord_login')
    
    context = {
        'guardian': guardian,
    }
    
    # Renderizar template baseado no role
    if guardian.is_guardian:
        return render(request, 'core/dashboard_guardian.html', context)
    else:
        return render(request, 'core/dashboard_usuario.html', context)


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
    """View para alternar status do Guardião - DEPRECATED"""
    
    def post(self, request):
        print("🚨 API ANTIGA CHAMADA: /api/status/")
        print("🚨 Esta API está DEPRECATED - use /api/guardians/status/")
        
        guardian_discord_id = request.session.get('guardian_id')
        if not guardian_discord_id:
            print("❌ Não autenticado")
            return JsonResponse({'error': 'Não autenticado'}, status=401)
        
        try:
            guardian = Guardian.objects.get(discord_id=guardian_discord_id)
            print(f"✅ Guardião encontrado: {guardian.discord_display_name} (ID: {guardian.discord_id})")
        except Guardian.DoesNotExist:
            print("❌ Perfil de Guardião não encontrado")
            return JsonResponse({'error': 'Perfil de Guardião não encontrado'}, status=404)
        
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            print(f"🔄 Status solicitado: {new_status}")
            
            if new_status not in ['online', 'offline']:
                print("❌ Status inválido")
                return JsonResponse({'error': 'Status inválido'}, status=400)
            
            old_status = guardian.status
            guardian.status = new_status
            guardian.save()
            print(f"✅ Status alterado de {old_status} para {new_status}")
            
            return JsonResponse({
                'success': True,
                'status': guardian.status,
                'status_display': guardian.get_status_display()
            })
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return JsonResponse({'error': str(e)}, status=500)


# ===== SISTEMA DE TREINAMENTO =====

def training_start(request):
    """Iniciar treinamento"""
    guardian_discord_id = request.session.get('guardian_id')
    
    if not guardian_discord_id:
        messages.error(request, 'Você precisa fazer login para acessar esta página.')
        return redirect('discord_login')
    
    try:
        guardian = Guardian.objects.get(discord_id=guardian_discord_id)
    except Guardian.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('discord_login')
    
    # Verificar se é elegível
    if not guardian.is_eligible_for_guardian:
        messages.error(request, 'Sua conta precisa ter pelo menos 3 meses para se tornar um Guardião.')
        return redirect('dashboard')
    
    # Verificar se já é Guardião
    if guardian.is_guardian:
        messages.info(request, 'Você já é um Guardião!')
        return redirect('dashboard')
    
    # Obter seções de treinamento
    sections = TrainingSection.objects.filter(is_active=True).order_by('order')
    
    context = {
        'guardian': guardian,
        'sections': sections,
    }
    
    return render(request, 'core/training_start.html', context)


def training_section(request, section_id):
    """Página de uma seção de treinamento"""
    guardian_discord_id = request.session.get('guardian_id')
    
    if not guardian_discord_id:
        messages.error(request, 'Você precisa fazer login para acessar esta página.')
        return redirect('discord_login')
    
    try:
        guardian = Guardian.objects.get(discord_id=guardian_discord_id)
    except Guardian.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('discord_login')
    
    # Verificar se é elegível
    if not guardian.is_eligible_for_guardian:
        messages.error(request, 'Sua conta precisa ter pelo menos 3 meses para se tornar um Guardião.')
        return redirect('dashboard')
    
    # Verificar se já é Guardião
    if guardian.is_guardian:
        messages.info(request, 'Você já é um Guardião!')
        return redirect('dashboard')
    
    try:
        section = TrainingSection.objects.get(id=section_id, is_active=True)
    except TrainingSection.DoesNotExist:
        messages.error(request, 'Seção de treinamento não encontrada.')
        return redirect('training_start')
    
    # Obter ou criar progresso
    progress, created = TrainingProgress.objects.get_or_create(
        guardian=guardian,
        section=section,
        defaults={'status': 'in_progress', 'started_at': timezone.now()}
    )
    
    # Obter exercícios da seção
    exercises = TrainingExercise.objects.filter(section=section, is_active=True).order_by('order')
    
    context = {
        'guardian': guardian,
        'section': section,
        'progress': progress,
        'exercises': exercises,
    }
    
    return render(request, 'core/training_section.html', context)


def training_exercise(request, exercise_id):
    """Página de um exercício específico"""
    guardian_discord_id = request.session.get('guardian_id')
    
    if not guardian_discord_id:
        messages.error(request, 'Você precisa fazer login para acessar esta página.')
        return redirect('discord_login')
    
    try:
        guardian = Guardian.objects.get(discord_id=guardian_discord_id)
    except Guardian.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('discord_login')
    
    # Verificar se é elegível
    if not guardian.is_eligible_for_guardian:
        messages.error(request, 'Sua conta precisa ter pelo menos 3 meses para se tornar um Guardião.')
        return redirect('dashboard')
    
    # Verificar se já é Guardião
    if guardian.is_guardian:
        messages.info(request, 'Você já é um Guardião!')
        return redirect('dashboard')
    
    try:
        exercise = TrainingExercise.objects.get(id=exercise_id, is_active=True)
    except TrainingExercise.DoesNotExist:
        messages.error(request, 'Exercício não encontrado.')
        return redirect('training_start')
    
    # Obter progresso da seção
    try:
        progress = TrainingProgress.objects.get(guardian=guardian, section=exercise.section)
    except TrainingProgress.DoesNotExist:
        messages.error(request, 'Progresso não encontrado.')
        return redirect('training_start')
    
    # Verificar se já respondeu este exercício
    existing_answer = TrainingAnswer.objects.filter(progress=progress, exercise=exercise).first()
    
    context = {
        'guardian': guardian,
        'exercise': exercise,
        'progress': progress,
        'existing_answer': existing_answer,
    }
    
    return render(request, 'core/training_exercise.html', context)


def training_answer(request, exercise_id):
    """Processar resposta de exercício"""
    if request.method != 'POST':
        return redirect('training_exercise', exercise_id=exercise_id)
    
    guardian_discord_id = request.session.get('guardian_id')
    
    if not guardian_discord_id:
        messages.error(request, 'Você precisa fazer login para acessar esta página.')
        return redirect('discord_login')
    
    try:
        guardian = Guardian.objects.get(discord_id=guardian_discord_id)
    except Guardian.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('discord_login')
    
    # Verificar se é elegível
    if not guardian.is_eligible_for_guardian:
        messages.error(request, 'Sua conta precisa ter pelo menos 3 meses para se tornar um Guardião.')
        return redirect('dashboard')
    
    # Verificar se já é Guardião
    if guardian.is_guardian:
        messages.info(request, 'Você já é um Guardião!')
        return redirect('dashboard')
    
    try:
        exercise = TrainingExercise.objects.get(id=exercise_id, is_active=True)
    except TrainingExercise.DoesNotExist:
        messages.error(request, 'Exercício não encontrado.')
        return redirect('training_start')
    
    # Obter progresso da seção
    try:
        progress = TrainingProgress.objects.get(guardian=guardian, section=exercise.section)
    except TrainingProgress.DoesNotExist:
        messages.error(request, 'Progresso não encontrado.')
        return redirect('training_start')
    
    # Verificar se já respondeu este exercício
    existing_answer = TrainingAnswer.objects.filter(progress=progress, exercise=exercise).first()
    if existing_answer:
        messages.info(request, 'Você já respondeu este exercício.')
        return redirect('training_exercise', exercise_id=exercise_id)
    
    # Processar resposta
    selected_answer = request.POST.get('answer')
    if not selected_answer or selected_answer not in ['a', 'b', 'c']:
        messages.error(request, 'Resposta inválida.')
        return redirect('training_exercise', exercise_id=exercise_id)
    
    # Verificar se está correto
    is_correct = selected_answer == exercise.correct_answer
    
    # Salvar resposta
    TrainingAnswer.objects.create(
        progress=progress,
        exercise=exercise,
        selected_answer=selected_answer,
        is_correct=is_correct
    )
    
    # Atualizar progresso
    progress.exercises_completed += 1
    if is_correct:
        progress.exercises_correct += 1
    
    # Verificar se completou todos os exercícios da seção
    total_exercises = TrainingExercise.objects.filter(section=exercise.section, is_active=True).count()
    if progress.exercises_completed >= total_exercises:
        progress.status = 'completed'
        progress.completed_at = timezone.now()
    
    progress.save()
    
    # Redirecionar para próxima seção ou prova final
    if progress.status == 'completed':
        if exercise.section.section_type == 'prova_final':
            # Verificar se passou na prova (máximo 1 erro)
            if progress.exercises_correct >= (total_exercises - 1):
                # APROVADO! Tornar-se Guardião
                guardian.role = 'guardian'
                guardian.save()
                messages.success(request, '🎉 Parabéns! Você foi aprovado e agora é um Guardião!')
                return redirect('dashboard')
            else:
                # REPROVADO
                progress.status = 'failed'
                progress.save()
                messages.error(request, 'Você não atingiu a pontuação necessária. Tente novamente após 24 horas.')
                return redirect('training_start')
        else:
            # Seção concluída, ir para próxima
            next_section = TrainingSection.objects.filter(
                is_active=True, 
                order__gt=exercise.section.order
            ).order_by('order').first()
            
            if next_section:
                messages.success(request, f'Seção "{exercise.section.title}" concluída!')
                return redirect('training_section', section_id=next_section.id)
            else:
                # Ir para prova final
                final_section = TrainingSection.objects.filter(
                    section_type='prova_final', 
                    is_active=True
                ).first()
                if final_section:
                    messages.success(request, 'Todas as seções concluídas! Agora é hora da prova final.')
                    return redirect('training_section', section_id=final_section.id)
                else:
                    messages.error(request, 'Prova final não encontrada.')
                    return redirect('training_start')
    else:
        # Exercício respondido, continuar na seção
        messages.success(request, f'Resposta {"correta" if is_correct else "incorreta"}! {exercise.explanation}')
        return redirect('training_exercise', exercise_id=exercise_id)


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