# 🚀 Guia de Deploy - ControlHS API

Este guia fornece instruções passo a passo para fazer deploy da API em produção.

---

## 📋 Pré-requisitos

- Ubuntu/Debian 20.04+ ou CentOS/RHEL 8+
- Python 3.9+
- PostgreSQL 12+
- Nginx
- Certbot (para HTTPS)
- Git

---

## 🔧 1. Preparação do Servidor

### 1.1 Atualizar sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Instalar dependências

```bash
# Python e pip
sudo apt install python3 python3-pip python3-venv -y

# PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Nginx
sudo apt install nginx -y

# Certbot para SSL
sudo apt install certbot python3-certbot-nginx -y

# Git
sudo apt install git -y
```

---

## 🗄️ 2. Configurar PostgreSQL

### 2.1 Criar banco de dados e usuário

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE controlhs;
CREATE USER controlhs_user WITH PASSWORD 'senha_super_segura_aqui';
GRANT ALL PRIVILEGES ON DATABASE controlhs TO controlhs_user;
\q
```

### 2.2 Configurar acesso remoto (opcional)

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Adicionar:
```
listen_addresses = 'localhost'  # Apenas localhost por segurança
```

---

## 📦 3. Clonar e Configurar Aplicação

### 3.1 Criar usuário para a aplicação

```bash
sudo adduser controlhs
sudo usermod -aG sudo controlhs
su - controlhs
```

### 3.2 Clonar repositório

```bash
cd /home/controlhs
git clone https://github.com/seu-usuario/login-controlhs.git
cd login-controlhs
```

### 3.3 Criar e ativar ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.4 Instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.5 Configurar variáveis de ambiente

```bash
cp .env.example .env
nano .env
```

**Configurar .env para PRODUÇÃO:**

```bash
# Database
DATABASE_URL=postgresql://controlhs_user:senha_super_segura_aqui@localhost:5432/controlhs

# Security - GERAR NOVA SECRET_KEY!
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=https://controlhs.com,https://app.controlhs.com

# Environment
ENVIRONMENT=production
DEBUG=False

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO
```

---

## 🔐 4. Gerar SECRET_KEY Segura

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copiar o resultado e colar no .env

---

## 🚀 5. Configurar Systemd Service

### 5.1 Criar arquivo de serviço

```bash
sudo nano /etc/systemd/system/controlhs-api.service
```

```ini
[Unit]
Description=ControlHS FastAPI Application
After=network.target postgresql.service

[Service]
Type=simple
User=controlhs
WorkingDirectory=/home/controlhs/login-controlhs
Environment="PATH=/home/controlhs/login-controlhs/venv/bin"
EnvironmentFile=/home/controlhs/login-controlhs/.env
ExecStart=/home/controlhs/login-controlhs/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/controlhs/access.log \
    --error-logfile /var/log/controlhs/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2 Criar diretório de logs

```bash
sudo mkdir -p /var/log/controlhs
sudo chown controlhs:controlhs /var/log/controlhs
```

### 5.3 Habilitar e iniciar serviço

```bash
sudo systemctl daemon-reload
sudo systemctl enable controlhs-api
sudo systemctl start controlhs-api
sudo systemctl status controlhs-api
```

---

## 🌐 6. Configurar Nginx

### 6.1 Criar configuração

```bash
sudo nano /etc/nginx/sites-available/controlhs-api
```

```nginx
# Redirecionar HTTP para HTTPS
server {
    listen 80;
    server_name authapicontrolhs.healthsafetytech.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name authapicontrolhs.healthsafetytech.com;

    # SSL (será configurado pelo Certbot)
    ssl_certificate /etc/letsencrypt/live/authapicontrolhs.healthsafetytech.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/authapicontrolhs.healthsafetytech.com/privkey.pem;

    # Configurações SSL modernas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Headers de segurança
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy para aplicação FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (se necessário)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Limite de upload
    client_max_body_size 10M;

    # Logs
    access_log /var/log/nginx/controlhs-api-access.log;
    error_log /var/log/nginx/controlhs-api-error.log;
}
```

### 6.2 Habilitar site

```bash
sudo ln -s /etc/nginx/sites-available/controlhs-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 7. Configurar HTTPS com Let's Encrypt

```bash
sudo certbot --nginx -d authapicontrolhs.healthsafetytech.com
```

Seguir instruções do Certbot.

### 7.1 Testar renovação automática

```bash
sudo certbot renew --dry-run
```

---

## 💾 8. Configurar Backups Automáticos

### 8.1 Criar diretório de backups

```bash
sudo mkdir -p /backups/controlhs
sudo chown controlhs:controlhs /backups/controlhs
```

### 8.2 Tornar script executável

```bash
chmod +x /home/controlhs/login-controlhs/scripts/backup_database.sh
```

### 8.3 Adicionar ao crontab

```bash
crontab -e
```

Adicionar (backup diário às 2h da manhã):

```cron
# Backup diário do banco ControlHS
0 2 * * * /home/controlhs/login-controlhs/scripts/backup_database.sh >> /var/log/controlhs/backup.log 2>&1
```

---

## 🔍 9. Monitoramento e Logs

### 9.1 Ver logs da aplicação

```bash
# Logs do serviço
sudo journalctl -u controlhs-api -f

# Logs da aplicação
tail -f /var/log/controlhs/access.log
tail -f /var/log/controlhs/error.log

# Logs do Nginx
tail -f /var/log/nginx/controlhs-api-access.log
tail -f /var/log/nginx/controlhs-api-error.log
```

### 9.2 Ver status do serviço

```bash
sudo systemctl status controlhs-api
```

### 9.3 Reiniciar aplicação

```bash
sudo systemctl restart controlhs-api
```

---

## 🔄 10. Atualização da Aplicação

```bash
# Ir para diretório
cd /home/controlhs/login-controlhs

# Fazer backup antes
/home/controlhs/login-controlhs/scripts/backup_database.sh

# Atualizar código
git pull origin main

# Ativar venv
source venv/bin/activate

# Atualizar dependências
pip install -r requirements.txt

# Reiniciar serviço
sudo systemctl restart controlhs-api

# Verificar status
sudo systemctl status controlhs-api
```

---

## ✅ 11. Checklist de Deploy

```
[ ] Servidor atualizado
[ ] PostgreSQL instalado e configurado
[ ] Banco de dados criado
[ ] Código clonado
[ ] Ambiente virtual criado
[ ] Dependências instaladas
[ ] .env configurado com valores de PRODUÇÃO
[ ] SECRET_KEY gerada
[ ] DEBUG=False no .env
[ ] Serviço systemd configurado
[ ] Nginx configurado
[ ] HTTPS configurado com Let's Encrypt
[ ] Backup automático configurado
[ ] Logs monitorados
[ ] Firewall configurado (portas 80, 443)
[ ] Aplicação testada
[ ] CORS configurado com domínios corretos
[ ] Rate limiting habilitado
```

---

## 🆘 12. Troubleshooting

### Aplicação não inicia

```bash
# Ver logs detalhados
sudo journalctl -u controlhs-api -n 100 --no-pager

# Testar manualmente
cd /home/controlhs/login-controlhs
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Erro de conexão com banco

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão manual
psql -h localhost -U controlhs_user -d controlhs
```

### Erro 502 Bad Gateway (Nginx)

```bash
# Verificar se aplicação está rodando
sudo systemctl status controlhs-api

# Ver porta em uso
sudo netstat -tlnp | grep 8000
```

### Certificado SSL expirado

```bash
# Renovar manualmente
sudo certbot renew

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## 📞 Suporte

Para mais ajuda:
- Documentação FastAPI: https://fastapi.tiangolo.com/
- Nginx Docs: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/docs/

---

## 🔐 Segurança Adicional

### Configurar Firewall (UFW)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

### Fail2Ban (proteção contra brute force)

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

**Deploy concluído! 🎉**
