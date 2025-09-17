"""
Forms para o Sistema Guardião
"""
from django import forms
from .models import Vote


class VoteForm(forms.Form):
    """Form para votação em denúncias"""
    
    VOTE_CHOICES = [
        ('improcedente', 'Improcedente'),
        ('intimidou', 'Intimidou'),
        ('grave', 'Grave'),
    ]
    
    vote_type = forms.ChoiceField(
        choices=VOTE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'vote-radio'}),
        label="Seu voto:"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vote_type'].widget.attrs.update({
            'class': 'vote-radio',
            'required': True
        })
