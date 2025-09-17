"""
Serializers para a API do Sistema Guardião
"""
from rest_framework import serializers
from .models import Guardian, Report, Vote, Message, Appeal, AppealVote


class GuardianSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Guardian"""
    
    class Meta:
        model = Guardian
        fields = [
            'id', 'discord_id', 'discord_username', 'discord_display_name',
            'avatar_url', 'status', 'level', 'points', 'total_service_hours',
            'correct_votes', 'incorrect_votes', 'accuracy_percentage',
            'created_at', 'updated_at', 'last_activity'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'accuracy_percentage']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Message"""
    
    class Meta:
        model = Message
        fields = [
            'id', 'original_user_id', 'original_message_id',
            'anonymized_username', 'content', 'timestamp', 'is_reported_user'
        ]


class VoteSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Vote"""
    
    guardian_name = serializers.CharField(source='guardian.discord_display_name', read_only=True)
    
    class Meta:
        model = Vote
        fields = [
            'id', 'vote_type', 'created_at', 'guardian_name'
        ]
        read_only_fields = ['id', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Report"""
    
    messages = MessageSerializer(many=True, read_only=True)
    votes = VoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'guild_id', 'channel_id', 'reported_user_id', 'reporter_user_id',
            'reason', 'status', 'punishment', 'votes_improcedente', 'votes_intimidou',
            'votes_grave', 'total_votes', 'created_at', 'completed_at',
            'messages', 'votes'
        ]
        read_only_fields = [
            'id', 'votes_improcedente', 'votes_intimidou', 'votes_grave',
            'total_votes', 'created_at', 'completed_at', 'punishment'
        ]


class AppealSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Appeal"""
    
    class Meta:
        model = Appeal
        fields = [
            'id', 'appellant_user_id', 'reason', 'status',
            'appeal_votes_improcedente', 'appeal_votes_intimidou',
            'appeal_votes_grave', 'appeal_total_votes',
            'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'appeal_votes_improcedente', 'appeal_votes_intimidou',
            'appeal_votes_grave', 'appeal_total_votes',
            'created_at', 'completed_at'
        ]


class AppealVoteSerializer(serializers.ModelSerializer):
    """Serializer para o modelo AppealVote"""
    
    guardian_name = serializers.CharField(source='guardian.discord_display_name', read_only=True)
    
    class Meta:
        model = AppealVote
        fields = [
            'id', 'vote_type', 'created_at', 'guardian_name'
        ]
        read_only_fields = ['id', 'created_at']


# Serializers para criação de objetos
class CreateReportSerializer(serializers.ModelSerializer):
    """Serializer para criar uma nova denúncia"""
    
    messages = MessageSerializer(many=True, required=False)
    
    class Meta:
        model = Report
        fields = [
            'guild_id', 'channel_id', 'reported_user_id', 'reporter_user_id',
            'reason', 'messages'
        ]
    
    def create(self, validated_data):
        messages_data = validated_data.pop('messages', [])
        report = Report.objects.create(**validated_data)
        
        for message_data in messages_data:
            Message.objects.create(report=report, **message_data)
        
        return report


class CreateVoteSerializer(serializers.ModelSerializer):
    """Serializer para criar um novo voto"""
    
    class Meta:
        model = Vote
        fields = ['report', 'guardian', 'vote_type']
    
    def validate(self, data):
        # Verificar se o Guardião já votou nesta denúncia
        if Vote.objects.filter(report=data['report'], guardian=data['guardian']).exists():
            raise serializers.ValidationError("Guardião já votou nesta denúncia")
        
        return data


class CreateAppealSerializer(serializers.ModelSerializer):
    """Serializer para criar uma nova apelação"""
    
    class Meta:
        model = Appeal
        fields = ['report', 'appellant_user_id', 'reason']
    
    def validate(self, data):
        # Verificar se já existe uma apelação para esta denúncia
        if Appeal.objects.filter(report=data['report']).exists():
            raise serializers.ValidationError("Já existe uma apelação para esta denúncia")
        
        return data


# Serializers para estatísticas
class StatsSerializer(serializers.Serializer):
    """Serializer para estatísticas do sistema"""
    
    total_reports = serializers.IntegerField()
    total_guardians = serializers.IntegerField()
    online_guardians = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    voting_reports = serializers.IntegerField()
    completed_reports = serializers.IntegerField()
    total_votes = serializers.IntegerField()
    votes_improcedente = serializers.IntegerField()
    votes_intimidou = serializers.IntegerField()
    votes_grave = serializers.IntegerField()
