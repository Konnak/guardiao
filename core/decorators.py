"""
Decorators customizados para o Sistema Guardião
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def guardian_required(view_func):
    """
    Decorator que verifica se o usuário está autenticado como Guardião
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('guardian_id'):
            messages.error(request, 'Você precisa fazer login para acessar esta página.')
            return redirect('discord_login')
        return view_func(request, *args, **kwargs)
    return wrapper
