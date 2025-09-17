#!/usr/bin/env python
"""
Arquivo de teste super simples para verificar se Python funciona na Discloud
"""
import os
import sys
import time

print("=" * 50)
print("🚀 TESTE SIMPLES INICIADO")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")
print("=" * 50)

# Testar imports básicos
try:
    import django
    print("✅ Django importado com sucesso")
    print(f"Django version: {django.get_version()}")
except Exception as e:
    print(f"❌ Erro ao importar Django: {e}")

try:
    import psycopg2
    print("✅ psycopg2 importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar psycopg2: {e}")

try:
    import discord
    print("✅ discord.py importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar discord.py: {e}")

print("=" * 50)
print("🔄 Teste de loop infinito (para manter aplicação rodando)")
print("Pressione Ctrl+C para parar")
print("=" * 50)

# Loop infinito para manter a aplicação rodando
counter = 0
while True:
    counter += 1
    print(f"⏰ Contador: {counter} - {time.strftime('%H:%M:%S')}")
    time.sleep(10)  # Espera 10 segundos
