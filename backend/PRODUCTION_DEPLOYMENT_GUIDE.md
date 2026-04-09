# 🚀 Production Deployment Guide
## Project: rag.gignaati.com — Windows Server, Port 2019

---

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Step 1 — Prepare the Environment](#step-1--prepare-the-environment)
4. [Step 2 — Configure Production .env](#step-2--configure-production-env)
5. [Step 3 — Update Application Config for Port 2019](#step-3--update-application-config-for-port-2019)
6. [Step 4 — Install & Configure PostgreSQL](#step-4--install--configure-postgresql)
7. [Step 5 — Install Ollama (LLM Service)](#step-5--install-ollama-llm-service)
8. [Step 6 — Run FastAPI as a Windows Service (NSSM)](#step-6--run-fastapi-as-a-windows-service-nssm)
9. [Step 7 — Set Up Nginx Reverse Proxy (Port 2019 → 8000)](#step-7--set-up-nginx-reverse-proxy-port-2019--8000)
10. [Step 8 — Windows Firewall Rules](#step-8--windows-firewall-rules)
11. [Step 9 — SSL/HTTPS with Let's Encrypt (Certbot)](#step-9--sslhttps-with-lets-encrypt-certbot)
12. [Step 10 — Final Nginx Config with SSL](#step-10--final-nginx-config-with-ssl)
13. [Step 11 — Verify Deployment](#step-11--verify-deployment)
14. [Maintenance & Operations](#maintenance--operations)

---

## 🏗️ Architecture Overview

```
Internet
   │
   ▼
[DNS: rag.gignaati.com → Your Server IP]
   │
   ▼
[Windows Firewall: Allow 443 / 2019]
   │
   ▼
[Nginx on Port 2019 / 443]  ← Handles SSL, static files, reverse proxy
   │
   ▼
[Uvicorn / FastAPI on Port 8000]  ← Python backend (internal only)
   │
   ├── [PostgreSQL on Port 5432]  ← Database (internal only)
   └── [Ollama on Port 11434]     ← LLM service (internal only)
```

> **Key Design**: Nginx listens on port 2019 (public), proxies to FastAPI on 8000 (private/local only). Never expose 8000 directly to the internet.

---

## ✅ Prerequisites

Install the following on your Windows Server:

| Tool | Download |
|------|----------|
| Python 3.10+ | https://www.python.org/downloads/ |
| PostgreSQL 15 | https://www.postgresql.org/download/windows/ |
| Nginx for Windows | https://nginx.org/en/download.html |
| NSSM (Service Manager) | https://nssm.cc/download |
| Ollama | https://ollama.com/download |
| Git | https://git-scm.com/download/win |

---

## Step 1 — Prepare the Environment

### 1.1 — Clone / Copy Project to Server

```powershell
# If using Git:
git clone <your-repo-url> D:\workbench

# Or copy your existing D:\workbench folder to production server
```

### 1.2 — Create Virtual Environment & Install Dependencies

Open **PowerShell as Administrator** and run:

```powershell
cd D:\workbench

# Create venv
python -m venv env

# Activate
env\Scripts\activate

# Install dependencies
pip install -r app\requirements.txt
```

---

## Step 2 — Configure Production .env

Edit `D:\workbench\.env` with production values:

```env
# ─── Server ───────────────────────────────────────
BASE_URL=https://rag.gignaati.com

# ─── Database ─────────────────────────────────────
DATABASE_URL=postgresql://raguser:YOUR_STRONG_PASSWORD@localhost:5432/ragdb

# ─── JWT Security ─────────────────────────────────
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=REPLACE_WITH_64_CHAR_RANDOM_HEX_STRING
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ─── Ollama (LLM) ─────────────────────────────────
OLLAMA_URL=http://localhost:11434/api/generate

# ─── Supabase (optional) ──────────────────────────
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# ─── N8N Webhook (optional) ───────────────────────
N8N_LEAD_WEBHOOK_URL=https://your-n8n.com/webhook/lead

# ─── WhatsApp (optional) ──────────────────────────
WHATSAPP_TOKEN=your-token
WHATSAPP_PHONE_ID=your-phone-id
WHATSAPP_VERIFY_TOKEN=swaran_verify_2024
```

> ⚠️ **Never commit .env to Git.** Add it to .gitignore.

---

## Step 3 — Update Application Config for Port 2019

### 3.1 — Update CORS in `app/main.py`

Replace the `origins` list with:

```python
origins = [
    "https://rag.gignaati.com",
    "http://rag.gignaati.com",
]
```

Remove all localhost/ngrok origins for production.

---

## Step 4 — Install & Configure PostgreSQL

### 4.1 — Install PostgreSQL
Download and install from https://www.postgresql.org/download/windows/

During installation set a strong password for the `postgres` superuser.

### 4.2 — Create Production Database & User

Open **pgAdmin** or run in PowerShell:

```powershell
# Open psql
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres
```

Then inside psql:

```sql
-- Create dedicated DB user
CREATE USER raguser WITH PASSWORD 'YOUR_STRONG_PASSWORD';

-- Create database
CREATE DATABASE ragdb OWNER raguser;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;

\q
```

### 4.3 — Ensure PostgreSQL Service is Running

```powershell
Get-Service -Name postgresql*
# Start if not running:
Start-Service -Name "postgresql-x64-15"
# Set to auto-start:
Set-Service -Name "postgresql-x64-15" -StartupType Automatic
```

---

## Step 5 — Install Ollama (LLM Service)

### 5.1 — Install & Pull Model

```powershell
# Install Ollama from https://ollama.com/download
# Then pull your model:
ollama pull llama3
# or whichever model your app uses
```

### 5.2 — Run Ollama as a Windows Service using NSSM

```powershell
# Download NSSM, extract to C:\nssm\
# Install Ollama as a service:
C:\nssm\nssm.exe install OllamaService "C:\Users\YOUR_USER\AppData\Local\Programs\Ollama\ollama.exe" "serve"

# Start the service:
Start-Service OllamaService
Set-Service OllamaService -StartupType Automatic
```

---

## Step 6 — Run FastAPI as a Windows Service (NSSM)

### 6.1 — Test the App Manually First

```powershell
cd D:\workbench
env\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
```

Visit http://127.0.0.1:8000/docs — if you see Swagger UI, it works.

### 6.2 — Create Windows Service with NSSM

```powershell
# Install service
C:\nssm\nssm.exe install FastAPIApp

# In the NSSM GUI that opens:
#   Path:           D:\workbench\env\Scripts\python.exe
#   Startup dir:    D:\workbench
#   Arguments:      -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

# OR via command line (no GUI):
C:\nssm\nssm.exe install FastAPIApp "D:\workbench\env\Scripts\python.exe" "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4"
C:\nssm\nssm.exe set FastAPIApp AppDirectory "D:\workbench"
C:\nssm\nssm.exe set FastAPIApp AppEnvironmentExtra "PYTHONPATH=D:\workbench"
C:\nssm\nssm.exe set FastAPIApp AppStdout "D:\workbench\logs\fastapi_out.log"
C:\nssm\nssm.exe set FastAPIApp AppStderr "D:\workbench\logs\fastapi_err.log"
C:\nssm\nssm.exe set FastAPIApp Start SERVICE_AUTO_START

# Create logs directory first:
mkdir D:\workbench\logs

# Start the service:
Start-Service FastAPIApp
```

### 6.3 — Verify Service is Running

```powershell
Get-Service FastAPIApp
# Should show: Running
```

---

## Step 7 — Set Up Nginx Reverse Proxy (Port 2019 → 8000)

### 7.1 — Install Nginx

Download **nginx/Windows** from https://nginx.org/en/download.html  
Extract to `C:\nginx\`

### 7.2 — Create Nginx Config (HTTP first, then add SSL)

Create/edit `C:\nginx\conf\nginx.conf`:

```nginx
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout  65;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

    # Gzip compression
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    server {
        listen       2019;
        server_name  rag.gignaati.com;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-Content-Type-Options "nosniff";
        add_header X-XSS-Protection "1; mode=block";

        # Proxy to FastAPI
        location / {
            limit_req zone=api burst=20 nodelay;

            proxy_pass         http://127.0.0.1:8000;
            proxy_http_version 1.1;
            proxy_set_header   Host              $host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_set_header   Upgrade           $http_upgrade;
            proxy_set_header   Connection        "upgrade";

            proxy_connect_timeout  60s;
            proxy_read_timeout     120s;
            proxy_send_timeout     120s;
        }

        # Serve static files directly (faster than going through Python)
        location /static/ {
            alias D:/workbench/static/;
            expires 7d;
            add_header Cache-Control "public, immutable";
        }

        location /frontend/ {
            alias D:/workbench/frontend/;
            expires 1d;
        }
    }
}
```

### 7.3 — Run Nginx as a Windows Service using NSSM

```powershell
C:\nssm\nssm.exe install NginxService "C:\nginx\nginx.exe"
C:\nssm\nssm.exe set NginxService AppDirectory "C:\nginx"
C:\nssm\nssm.exe set NginxService Start SERVICE_AUTO_START

Start-Service NginxService
```

### 7.4 — Test Nginx Config

```powershell
C:\nginx\nginx.exe -t
# Should output: configuration file test is successful
```

---

## Step 8 — Windows Firewall Rules

Open **PowerShell as Administrator**:

```powershell
# Allow port 2019 (your public port)
New-NetFirewallRule -DisplayName "Nginx Port 2019" -Direction Inbound -Protocol TCP -LocalPort 2019 -Action Allow

# Allow HTTPS (443) — for SSL later
New-NetFirewallRule -DisplayName "HTTPS 443" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow

# Allow HTTP (80) — needed for Let's Encrypt verification
New-NetFirewallRule -DisplayName "HTTP 80" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow

# Block direct access to FastAPI from outside (security)
New-NetFirewallRule -DisplayName "Block External FastAPI" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress Internet -Action Block
```

---

## Step 9 — SSL/HTTPS with Let's Encrypt (Certbot)

### 9.1 — Install Certbot for Windows

Download from: https://certbot.eff.org/instructions?ws=other&os=windows

```powershell
# Run Certbot (stop Nginx first, it needs port 80)
Stop-Service NginxService

# Get certificate (standalone mode)
certbot certonly --standalone -d rag.gignaati.com

# Certificates will be saved to:
# C:\Certbot\live\rag.gignaati.com\fullchain.pem
# C:\Certbot\live\rag.gignaati.com\privkey.pem

# Restart Nginx after cert obtained
Start-Service NginxService
```

### 9.2 — Auto-Renewal (Task Scheduler)

```powershell
# Create a scheduled task to auto-renew every 60 days
$action = New-ScheduledTaskAction -Execute "certbot" -Argument "renew --quiet"
$trigger = New-ScheduledTaskTrigger -Daily -At "3:00AM"
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "CertbotRenew" -RunLevel Highest
```

---

## Step 10 — Final Nginx Config with SSL

Update `C:\nginx\conf\nginx.conf` to redirect HTTP → HTTPS and serve on port 2019 with SSL:

```nginx
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout  65;

    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # Redirect HTTP → HTTPS
    server {
        listen 80;
        server_name rag.gignaati.com;
        return 301 https://$host:2019$request_uri;
    }

    # Main HTTPS server on port 2019
    server {
        listen       2019 ssl;
        server_name  rag.gignaati.com;

        # SSL Certificates
        ssl_certificate     C:/Certbot/live/rag.gignaati.com/fullchain.pem;
        ssl_certificate_key C:/Certbot/live/rag.gignaati.com/privkey.pem;

        # SSL Settings
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         HIGH:!aNULL:!MD5;
        ssl_session_cache   shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-Content-Type-Options "nosniff";
        add_header X-XSS-Protection "1; mode=block";

        # Proxy to FastAPI
        location / {
            limit_req zone=api burst=20 nodelay;

            proxy_pass         http://127.0.0.1:8000;
            proxy_http_version 1.1;
            proxy_set_header   Host              $host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_set_header   Upgrade           $http_upgrade;
            proxy_set_header   Connection        "upgrade";

            proxy_connect_timeout  60s;
            proxy_read_timeout     120s;
            proxy_send_timeout     120s;
        }

        location /static/ {
            alias D:/workbench/static/;
            expires 7d;
            add_header Cache-Control "public, immutable";
        }

        location /frontend/ {
            alias D:/workbench/frontend/;
            expires 1d;
        }
    }
}
```

Reload Nginx after changes:
```powershell
C:\nginx\nginx.exe -s reload
```

---

## Step 11 — Verify Deployment

### 11.1 — Check All Services

```powershell
Get-Service FastAPIApp, NginxService, OllamaService, postgresql-x64-15
# All should show: Running
```

### 11.2 — Test Endpoints

```powershell
# Test FastAPI directly (internal)
Invoke-WebRequest http://127.0.0.1:8000/docs

# Test via Nginx (public)
Invoke-WebRequest https://rag.gignaati.com:2019/docs

# Test API health
Invoke-WebRequest https://rag.gignaati.com:2019/api/v1/
```

### 11.3 — Check Logs

```powershell
# FastAPI logs
Get-Content D:\workbench\logs\fastapi_out.log -Tail 50

# Nginx logs
Get-Content C:\nginx\logs\error.log -Tail 50
Get-Content C:\nginx\logs\access.log -Tail 50
```

---

## 🔧 Maintenance & Operations

### Restart Services

```powershell
Restart-Service FastAPIApp
Restart-Service NginxService
C:\nginx\nginx.exe -s reload   # Graceful reload (no downtime)
```

### Update App Code

```powershell
cd D:\workbench
git pull origin main            # Pull latest code
env\Scripts\activate
pip install -r app\requirements.txt  # Install any new deps
Restart-Service FastAPIApp      # Restart app
```

### View Live Logs

```powershell
Get-Content D:\workbench\logs\fastapi_out.log -Wait -Tail 20
```

---

## 🔐 Production Security Checklist

- [ ] `SECRET_KEY` is a 64-char random hex string (not default)
- [ ] Database password is strong and not `postgres/postgres`
- [ ] Port 8000 is blocked from external internet access
- [ ] `.env` is NOT committed to Git
- [ ] SSL certificate is installed and HTTPS is enforced
- [ ] `--reload` flag is removed from uvicorn (production only)
- [ ] CORS origins contain only `https://rag.gignaati.com`
- [ ] Ollama is bound to localhost only (default behavior)
- [ ] PostgreSQL listens on localhost only (default behavior)
- [ ] Firewall rules are active
- [ ] Windows Defender / Antivirus exclusions set for D:\workbench\venv

---

## 📁 Final Service Summary

| Service | Tool | Port | Auto-Start |
|---------|------|------|------------|
| FastAPI Backend | NSSM → Uvicorn | 8000 (internal) | ✅ |
| Nginx Reverse Proxy | NSSM → Nginx | 2019 (public) | ✅ |
| Ollama LLM | NSSM → Ollama | 11434 (internal) | ✅ |
| PostgreSQL | Windows Service | 5432 (internal) | ✅ |

---

*Generated for project at D:\workbench | Target: https://rag.gignaati.com:2019*
