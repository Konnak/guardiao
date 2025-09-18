from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Guardian(models.Model):
    """Modelo para representar um Guardião do sistema"""
    
    ROLE_CHOICES = [
        ('usuario', 'Usuário'),
        ('guardian', 'Guardião'),
    ]
    
    STATUS_CHOICES = [
        ('online', 'Em Serviço'),
        ('offline', 'Fora de Serviço'),
    ]
    
    LEVEL_CHOICES = [
        (1, 'Novato'),
        (2, 'Aprendiz'),
        (3, 'Experiente'),
        (4, 'Veterano'),
        (5, 'Mestre'),
    ]
    
    discord_id = models.BigIntegerField(unique=True, verbose_name="ID do Discord")
    discord_username = models.CharField(max_length=100, verbose_name="Nome de Usuário")
    discord_display_name = models.CharField(max_length=100, verbose_name="Nome de Exibição")
    avatar_url = models.URLField(blank=True, null=True, verbose_name="URL do Avatar")
    
    # Sistema de papéis e treinamento
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='usuario', verbose_name="Papel")
    discord_account_created_at = models.DateTimeField(null=True, blank=True, verbose_name="Data de Criação da Conta Discord")
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline', verbose_name="Status")
    level = models.IntegerField(choices=LEVEL_CHOICES, default=1, verbose_name="Nível")
    points = models.IntegerField(default=0, verbose_name="Pontos")
    
    total_service_hours = models.FloatField(default=0.0, verbose_name="Horas Totais de Serviço")
    correct_votes = models.IntegerField(default=0, verbose_name="Votos Corretos")
    incorrect_votes = models.IntegerField(default=0, verbose_name="Votos Incorretos")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    last_activity = models.DateTimeField(default=timezone.now, verbose_name="Última Atividade")
    
    class Meta:
        verbose_name = "Guardião"
        verbose_name_plural = "Guardiões"
        ordering = ['-points', '-level']
    
    def __str__(self):
        return f"{self.discord_display_name} (Nível {self.level})"
    
    @property
    def accuracy_percentage(self):
        """Calcula a porcentagem de precisão dos votos"""
        total_votes = self.correct_votes + self.incorrect_votes
        if total_votes == 0:
            return 0
        return round((self.correct_votes / total_votes) * 100, 2)
    
    @property
    def is_eligible_for_guardian(self):
        """Verifica se o usuário é elegível para se tornar Guardião (conta > 3 meses)"""
        if not self.discord_account_created_at:
            return False
        
        from datetime import timedelta
        three_months_ago = timezone.now() - timedelta(days=90)
        return self.discord_account_created_at <= three_months_ago
    
    @property
    def is_guardian(self):
        """Verifica se o usuário é um Guardião"""
        return self.role == 'guardian'
    
    @property
    def is_usuario(self):
        """Verifica se o usuário é apenas um Usuário"""
        return self.role == 'usuario'
    
    @property
    def days_until_eligible(self):
        """Calcula quantos dias faltam para ser elegível (se não for elegível)"""
        if self.is_eligible_for_guardian:
            return 0
        
        if not self.discord_account_created_at:
            # Se não temos a data, assumir que é elegível (conta antiga)
            return 0
        
        from datetime import timedelta
        days_since_creation = (timezone.now() - self.discord_account_created_at).days
        return max(0, 90 - days_since_creation)


class Report(models.Model):
    """Modelo para representar uma denúncia"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('voting', 'Em Votação'),
        ('completed', 'Concluída'),
        ('appealed', 'Em Apelação'),
        ('closed', 'Fechada'),
    ]
    
    PUNISHMENT_CHOICES = [
        ('none', 'Nenhuma'),
        ('mute_1h', 'Mute 1 hora'),
        ('mute_12h', 'Mute 12 horas'),
        ('ban_24h', 'Banimento 24 horas'),
    ]
    
    # IDs do Discord
    guild_id = models.BigIntegerField(verbose_name="ID do Servidor")
    channel_id = models.BigIntegerField(verbose_name="ID do Canal")
    reported_user_id = models.BigIntegerField(verbose_name="ID do Usuário Denunciado")
    reporter_user_id = models.BigIntegerField(verbose_name="ID do Denunciante")
    
    # Informações da denúncia
    reason = models.TextField(blank=True, null=True, verbose_name="Motivo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    punishment = models.CharField(max_length=20, choices=PUNISHMENT_CHOICES, default='none', verbose_name="Punição")
    
    # Contadores de votos
    votes_improcedente = models.IntegerField(default=0, verbose_name="Votos Improcedente")
    votes_intimidou = models.IntegerField(default=0, verbose_name="Votos Intimidou")
    votes_grave = models.IntegerField(default=0, verbose_name="Votos Grave")
    total_votes = models.IntegerField(default=0, verbose_name="Total de Votos")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Concluído em")
    
    class Meta:
        verbose_name = "Denúncia"
        verbose_name_plural = "Denúncias"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Denúncia #{self.id} - Usuário {self.reported_user_id}"
    
    @property
    def is_completed(self):
        """Verifica se a denúncia foi concluída (5 votos)"""
        return self.total_votes >= 5
    
    def calculate_punishment(self):
        """Calcula a punição baseada nos votos"""
        if self.total_votes < 5:
            return 'none'
        
        # Regras de punição conforme especificado no BASE.md
        if self.votes_improcedente >= 3:
            return 'none'
        elif self.votes_intimidou == 3 and self.votes_grave == 0:
            return 'mute_1h'
        elif self.votes_intimidou == 3 and self.votes_grave == 2:
            return 'mute_12h'
        elif self.votes_grave == 3 and self.votes_improcedente == 2:
            return 'mute_1h'
        elif self.votes_grave == 3 and self.votes_intimidou == 2:
            return 'ban_24h'
        elif self.votes_grave >= 4:
            return 'ban_24h'
        else:
            return 'none'
    
    def get_punishment_display(self):
        """Retorna a descrição da punição"""
        punishment_display = {
            'none': 'Nenhuma',
            'mute_1h': 'Mute de 1 hora',
            'mute_12h': 'Mute de 12 horas',
            'ban_24h': 'Banimento de 24 horas',
        }
        return punishment_display.get(self.punishment, 'Desconhecida')


class Vote(models.Model):
    """Modelo para representar um voto de um Guardião"""
    
    VOTE_CHOICES = [
        ('improcedente', 'Improcedente'),
        ('intimidou', 'Intimidou'),
        ('grave', 'Grave'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='votes', verbose_name="Denúncia")
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, verbose_name="Guardião")
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES, verbose_name="Tipo de Voto")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    class Meta:
        verbose_name = "Voto"
        verbose_name_plural = "Votos"
        unique_together = ['report', 'guardian']  # Um Guardião só pode votar uma vez por denúncia
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.guardian.discord_display_name} votou {self.get_vote_type_display()} na denúncia #{self.report.id}"


class Message(models.Model):
    """Modelo para armazenar mensagens das denúncias"""
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='messages', verbose_name="Denúncia")
    
    # IDs originais do Discord
    original_user_id = models.BigIntegerField(verbose_name="ID Original do Usuário")
    original_message_id = models.BigIntegerField(verbose_name="ID Original da Mensagem")
    
    # Dados anonimizados
    anonymized_username = models.CharField(max_length=100, verbose_name="Nome Anonimizado")
    content = models.TextField(verbose_name="Conteúdo da Mensagem")
    
    # Mídias anexadas
    has_attachments = models.BooleanField(default=False, verbose_name="Tem Anexos")
    attachments_info = models.JSONField(blank=True, null=True, verbose_name="Informações dos Anexos")
    
    # Metadados
    timestamp = models.DateTimeField(verbose_name="Timestamp")
    is_reported_user = models.BooleanField(default=False, verbose_name="É o Usuário Denunciado")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Mensagem de {self.anonymized_username} na denúncia #{self.report.id}"


class Appeal(models.Model):
    """Modelo para representar uma apelação"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('voting', 'Em Votação'),
        ('approved', 'Aprovada'),
        ('rejected', 'Rejeitada'),
    ]
    
    report = models.OneToOneField(Report, on_delete=models.CASCADE, related_name='appeal', verbose_name="Denúncia")
    appellant_user_id = models.BigIntegerField(verbose_name="ID do Apelante")
    
    reason = models.TextField(verbose_name="Motivo da Apelação")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    
    # Contadores de votos da apelação
    appeal_votes_improcedente = models.IntegerField(default=0, verbose_name="Votos Improcedente (Apelação)")
    appeal_votes_intimidou = models.IntegerField(default=0, verbose_name="Votos Intimidou (Apelação)")
    appeal_votes_grave = models.IntegerField(default=0, verbose_name="Votos Grave (Apelação)")
    appeal_total_votes = models.IntegerField(default=0, verbose_name="Total de Votos (Apelação)")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Concluído em")
    
    class Meta:
        verbose_name = "Apelação"
        verbose_name_plural = "Apelações"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Apelação da denúncia #{self.report.id}"
    
    def calculate_appeal_result(self):
        """Calcula o resultado da apelação"""
        if self.appeal_total_votes < 5:
            return None
        
        # Lógica de apelação: maioria decide
        if self.appeal_votes_improcedente >= 3:
            return 'approved'  # Apelação aprovada - punição revogada
        elif self.appeal_votes_intimidou >= 3 or self.appeal_votes_grave >= 3:
            return 'rejected'  # Apelação rejeitada - punição mantida
        else:
            return None  # Ainda não há resultado claro
    
    def process_appeal_result(self):
        """Processa o resultado da apelação"""
        result = self.calculate_appeal_result()
        
        if result == 'approved':
            self.status = 'approved'
            # Revogar punição original
            self.report.punishment = 'none'
            self.report.status = 'closed'
            self.report.save()
            
            # Penalizar Guardiões que votaram incorretamente
            self.penalize_original_guardians()
            
        elif result == 'rejected':
            self.status = 'rejected'
            # Manter punição original
            # Aplicar punição dobrada se necessário
            self.apply_doubled_punishment()
        
        if result:
            self.completed_at = timezone.now()
            self.save()
    
    def penalize_original_guardians(self):
        """Penaliza Guardiões que votaram incorretamente na denúncia original"""
        original_votes = Vote.objects.filter(report=self.report)
        
        for vote in original_votes:
            if vote.vote_type in ['intimidou', 'grave']:
                guardian = vote.guardian
                guardian.points = max(0, guardian.points - 3)  # Perder 3 pontos
                guardian.save()
    
    def apply_doubled_punishment(self):
        """Aplica punição dobrada se necessário"""
        # Implementar lógica de punição dobrada conforme especificado
        pass


class AppealVote(models.Model):
    """Modelo para representar um voto em uma apelação"""
    
    VOTE_CHOICES = [
        ('improcedente', 'Improcedente'),
        ('intimidou', 'Intimidou'),
        ('grave', 'Grave'),
    ]
    
    appeal = models.ForeignKey(Appeal, on_delete=models.CASCADE, related_name='votes', verbose_name="Apelação")
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, verbose_name="Guardião")
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES, verbose_name="Tipo de Voto")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    class Meta:
        verbose_name = "Voto de Apelação"
        verbose_name_plural = "Votos de Apelação"
        unique_together = ['appeal', 'guardian']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.guardian.discord_display_name} votou {self.get_vote_type_display()} na apelação #{self.appeal.id}"


class VotingSession(models.Model):
    """Modelo para controlar sessões de votação simultâneas"""
    
    STATUS_CHOICES = [
        ('waiting', 'Aguardando Guardiões'),
        ('voting', 'Em Votação'),
        ('completed', 'Concluída'),
        ('cancelled', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, verbose_name="Denúncia")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Iniciado em")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Concluído em")
    
    # Controle de tempo
    voting_deadline = models.DateTimeField(null=True, blank=True, verbose_name="Prazo para Votação")
    
    class Meta:
        verbose_name = "Sessão de Votação"
        verbose_name_plural = "Sessões de Votação"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sessão #{self.id} - Denúncia #{self.report.id} ({self.get_status_display()})"
    
    def is_expired(self):
        """Verifica se a sessão expirou"""
        if not self.voting_deadline:
            return False
        return timezone.now() > self.voting_deadline
    
    def get_active_guardians(self):
        """Retorna os Guardiões ativos na sessão"""
        return self.sessionguardian_set.filter(is_active=True)


class SessionGuardian(models.Model):
    """Modelo para controlar Guardiões em sessões de votação"""
    
    session = models.ForeignKey(VotingSession, on_delete=models.CASCADE, verbose_name="Sessão")
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, verbose_name="Guardião")
    
    is_active = models.BooleanField(default=True, verbose_name="Ativo na Sessão")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Entrou em")
    left_at = models.DateTimeField(null=True, blank=True, verbose_name="Saiu em")
    
    # Controle de votação
    has_voted = models.BooleanField(default=False, verbose_name="Já Votou")
    vote_type = models.CharField(max_length=20, choices=Vote.VOTE_CHOICES, null=True, blank=True, verbose_name="Tipo de Voto")
    voted_at = models.DateTimeField(null=True, blank=True, verbose_name="Votou em")
    
    class Meta:
        verbose_name = "Guardião da Sessão"
        verbose_name_plural = "Guardiões da Sessão"
        unique_together = ['session', 'guardian']
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.guardian.discord_display_name} na Sessão #{self.session.id}"


class ReportQueue(models.Model):
    """Modelo para controlar a fila de denúncias pendentes"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('assigned', 'Atribuída'),
        ('processing', 'Processando'),
        ('completed', 'Concluída'),
        ('cancelled', 'Cancelada'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, verbose_name="Denúncia")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    
    priority = models.IntegerField(default=0, verbose_name="Prioridade")  # Maior número = maior prioridade
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name="Atribuída em")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Concluída em")
    
    class Meta:
        verbose_name = "Fila de Denúncias"
        verbose_name_plural = "Fila de Denúncias"
        ordering = ['-priority', 'created_at']
    
    def __str__(self):
        return f"Fila #{self.id} - Denúncia #{self.report.id} ({self.get_status_display()})"


# ===== SISTEMA DE TREINAMENTO =====

class TrainingSection(models.Model):
    """Modelo para seções do treinamento"""
    
    SECTION_CHOICES = [
        ('principios', 'Os Princípios do Guardião'),
        ('classificacao', 'Classificando uma Denúncia'),
        ('prova_final', 'Prova Final'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Título")
    section_type = models.CharField(max_length=20, choices=SECTION_CHOICES, verbose_name="Tipo de Seção")
    content = models.TextField(verbose_name="Conteúdo")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Seção de Treinamento"
        verbose_name_plural = "Seções de Treinamento"
        ordering = ['order']
    
    def __str__(self):
        return f"{self.title} ({self.get_section_type_display()})"


class TrainingExercise(models.Model):
    """Modelo para exercícios do treinamento"""
    
    section = models.ForeignKey(TrainingSection, on_delete=models.CASCADE, related_name='exercises', verbose_name="Seção")
    question = models.TextField(verbose_name="Pergunta")
    
    # Opções de resposta
    option_a = models.CharField(max_length=500, verbose_name="Opção A")
    option_b = models.CharField(max_length=500, verbose_name="Opção B")
    option_c = models.CharField(max_length=500, verbose_name="Opção C", blank=True, null=True)
    
    # Resposta correta
    correct_answer = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C')], verbose_name="Resposta Correta")
    
    # Explicação da resposta
    explanation = models.TextField(verbose_name="Explicação")
    
    order = models.IntegerField(default=0, verbose_name="Ordem")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Exercício de Treinamento"
        verbose_name_plural = "Exercícios de Treinamento"
        ordering = ['section', 'order']
    
    def __str__(self):
        return f"{self.section.title} - {self.question[:50]}..."


class TrainingProgress(models.Model):
    """Modelo para acompanhar o progresso do treinamento"""
    
    STATUS_CHOICES = [
        ('not_started', 'Não Iniciado'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído'),
        ('failed', 'Reprovado'),
    ]
    
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name='training_progress', verbose_name="Guardião")
    section = models.ForeignKey(TrainingSection, on_delete=models.CASCADE, verbose_name="Seção")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name="Status")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Iniciado em")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Concluído em")
    
    # Para exercícios
    exercises_completed = models.IntegerField(default=0, verbose_name="Exercícios Concluídos")
    exercises_correct = models.IntegerField(default=0, verbose_name="Exercícios Corretos")
    
    # Para prova final
    final_exam_score = models.IntegerField(default=0, verbose_name="Pontuação da Prova Final")
    final_exam_attempts = models.IntegerField(default=0, verbose_name="Tentativas da Prova Final")
    last_exam_attempt = models.DateTimeField(null=True, blank=True, verbose_name="Última Tentativa da Prova")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Progresso do Treinamento"
        verbose_name_plural = "Progressos do Treinamento"
        unique_together = ['guardian', 'section']
        ordering = ['guardian', 'section__order']
    
    def __str__(self):
        return f"{self.guardian.discord_display_name} - {self.section.title} ({self.get_status_display()})"
    
    @property
    def can_retake_exam(self):
        """Verifica se pode refazer a prova (após 24 horas)"""
        if not self.last_exam_attempt:
            return True
        
        from datetime import timedelta
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        return self.last_exam_attempt <= twenty_four_hours_ago
    
    @property
    def accuracy_percentage(self):
        """Calcula a porcentagem de acerto nos exercícios"""
        if self.exercises_completed == 0:
            return 0
        return round((self.exercises_correct / self.exercises_completed) * 100, 2)


class TrainingAnswer(models.Model):
    """Modelo para armazenar respostas dos exercícios"""
    
    progress = models.ForeignKey(TrainingProgress, on_delete=models.CASCADE, related_name='answers', verbose_name="Progresso")
    exercise = models.ForeignKey(TrainingExercise, on_delete=models.CASCADE, verbose_name="Exercício")
    
    selected_answer = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C')], verbose_name="Resposta Selecionada")
    is_correct = models.BooleanField(verbose_name="Correta")
    
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Respondido em")
    
    class Meta:
        verbose_name = "Resposta de Exercício"
        verbose_name_plural = "Respostas de Exercícios"
        unique_together = ['progress', 'exercise']
        ordering = ['answered_at']
    
    def __str__(self):
        return f"{self.progress.guardian.discord_display_name} - {self.exercise.question[:30]}... ({'✓' if self.is_correct else '✗'})"