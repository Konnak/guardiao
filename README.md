# Sistema Guardião

Uma plataforma completa de moderação para servidores Discord, inspirada no sistema de Guardiões do Habbo Hotel. O sistema é composto por um website (painel de controle e análise de denúncias) e um bot de Discord totalmente integrados.

## 🚀 Características

- **Sistema de Denúncias**: Comando `/report` para reportar violações
- **Análise Colaborativa**: Guardiões analisam denúncias de forma anônima
- **Votação Transparente**: Sistema de votação com 3 opções (Improcedente, Intimidou, Grave)
- **Punições Automáticas**: Aplicação automática de punições baseada nos votos
- **Sistema de Apelação**: Usuários podem solicitar revisão de punições
- **Dashboard Completo**: Interface web para gerenciamento e análise
- **Autenticação Discord**: Login seguro via OAuth2

## 🛠️ Tecnologias

- **Backend**: Django 4.2.7
- **Bot Discord**: discord.py 2.3.2
- **Banco de Dados**: PostgreSQL v17
- **Frontend**: HTML5, CSS3, JavaScript
- **Hospedagem**: Discloud

## 📋 Pré-requisitos

- Python 3.10+
- PostgreSQL v17
- Conta Discord com aplicação configurada
- Conta Discloud para hospedagem

## 🔧 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/Konnak/guardiao.git
cd guardiao
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` baseado no `discloud.env`:

```bash
cp discloud.env .env
```

Edite o arquivo `.env` com suas credenciais:

```env
# Discord Bot Credentials
DISCORD_BOT_TOKEN=seu_token_aqui
DISCORD_CLIENT_ID=seu_client_id_aqui
DISCORD_CLIENT_SECRET=seu_client_secret_aqui

# Database Configuration
DB_NAME=guardiaodatabase
DB_USER=guardiao
DB_PASSWORD=sua_senha_aqui
DB_HOST=postgresql
DB_PORT=5432

# Django Settings
SECRET_KEY=sua_secret_key_aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Site URL
SITE_URL=http://localhost:8080
```

### 4. Execute as migrações

```bash
python manage.py migrate
```

### 5. Crie um superusuário (opcional)

```bash
python manage.py createsuperuser
```

## 🚀 Execução

### Desenvolvimento Local

Para executar apenas o servidor web:
```bash
python manage.py runserver
```

Para executar apenas o bot Discord:
```bash
python manage.py runbot
```

Para executar ambos simultaneamente:
```bash
python manage.py runall
```

### Produção (Discloud)

O sistema está configurado para ser executado na Discloud. Use o arquivo `discloud.config` para configuração.

## 📖 Uso

### Para Usuários

1. **Reportar Violação**: Use o comando `/report @usuário motivo` no Discord
2. **Solicitar Apelação**: Acesse o site para solicitar revisão de punições

### Para Guardiões

1. **Login**: Acesse o site e faça login com Discord
2. **Definir Status**: Use o comando `/status online` ou `/status offline` no Discord
3. **Analisar Denúncias**: Acesse o dashboard para ver denúncias pendentes
4. **Votar**: Analise o contexto e vote em Improcedente, Intimidou ou Grave

### Para Administradores

1. **Painel Admin**: Acesse `/admin/` para gerenciar o sistema
2. **Estatísticas**: Visualize dados gerais do sistema
3. **Gerenciamento**: Gerencie Guardiões e denúncias

## 🎯 Sistema de Votação

### Regras de Punição

- **3+ votos Improcedente** → Denúncia fechada sem ação
- **Exatamente 3 Intimidou** → Mute de 1 hora
- **3 Intimidou + 2 Grave** → Mute de 12 horas
- **3 Grave + 2 Improcedente** → Mute de 1 hora
- **3 Grave + 2 Intimidou** → Banimento de 24 horas + Notificação para Admins
- **4 ou 5 Grave** → Banimento de 24 horas + Notificação para Admins

### Sistema de Pontos

- **+1 ponto** por cada hora com status "Em Serviço"
- **+1 ponto** se o voto coincidir com o resultado final
- **-3 pontos** se a punição for revogada na apelação

## 🔒 Segurança

- Todas as credenciais são gerenciadas via variáveis de ambiente
- Autenticação segura via Discord OAuth2
- Anonimização de dados de usuários
- Validação de permissões em todas as operações

## 📁 Estrutura do Projeto

```
guardiao/
├── core/                    # App principal (models, views, templates)
├── bot/                     # Bot Discord
├── guardiao/               # Configurações Django
├── static/                 # Arquivos estáticos
├── templates/              # Templates HTML
├── manage.py               # Gerenciador principal
├── requirements.txt        # Dependências Python
├── discloud.config         # Configuração Discloud
└── README.md              # Este arquivo
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte, entre em contato através do Discord ou abra uma issue no GitHub.

---

**Sistema Guardião** - Mantendo os servidores Discord seguros e acolhedores! 🛡️
