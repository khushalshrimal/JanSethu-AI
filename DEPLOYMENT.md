# JanSethu AI 2.0 — Production Deployment Guide

This guide outlines step-by-step instructions for deploying JanSethu AI 2.0 to a production environment behind HTTPS with PostgreSQL, containerization, and telephony provider webhooks.

---

## 🏗️ Architecture Overview

```text
                                 INTERNET
                                    │
                                    ▼
                          HTTPS Reverse Proxy (Nginx / Caddy / Cloudflare)
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                        ▼                       ▼
                   React PWA           FastAPI Backend (Uvicorn / Docker)
               (Vite Static Build)              │
                                       ┌────────┴────────┐
                                       ▼                 ▼
                                  PostgreSQL       Telephony / SMS
                                 (DB Engine)          Providers
```

---

## 📋 Prerequisites & Environment Variables

Create a production `.env` file based on `.env.example`:

```env
APP_ENV=production
DEBUG=false

# Secrets (Must be generated randomly!)
SECRET_KEY=<64-byte-secure-random-hex>
WEBHOOK_SECRET=<secure-random-token>

# Database
DATABASE_URL=postgresql://jansethu_user:<DB_PASSWORD>@<DB_HOST>:5432/jansethudb

# Network & Webhooks
PUBLIC_BASE_URL=https://jansethu.example.com
CORS_ORIGINS=https://jansethu.example.com,https://admin.jansethu.example.com

# Telephony & SMS Providers
TELEPHONY_PROVIDER=development  # Change to 'twilio' or 'exotel' when live
SMS_PROVIDER=development        # Change to 'twilio' or 'msg91' when live
```

---

## 🗄️ Step 1: Provision & Migrate Production PostgreSQL Database

1. Provision PostgreSQL 14+ database instance.
2. Run database migrations safely without overwriting data:

```bash
cd backend
# Set DATABASE_URL in environment before running
python -c "from alembic.config import main; main()" upgrade head
```

---

## 🚀 Step 2: Deploy Backend Service (FastAPI)

### Option A: Docker Compose (Production-Like Mode)

```bash
docker-compose up -d --build
```

### Option B: Bare-Metal / Systemd / VirtualEnv

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run ASGI server with Gunicorn / Uvicorn workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🌐 Step 3: Deploy Frontend PWA Static Build

```bash
cd frontend
npm install
VITE_API_URL=https://jansethu.example.com/api/v1 npm run build
```

Upload the static output in `dist/` to Nginx, S3 + CloudFront, Vercel, or Netlify.

---

## 🔒 Step 4: Configure HTTPS & Reverse Proxy (Nginx Example)

```nginx
server {
    listen 443 ssl http2;
    server_name jansethu.example.com;

    ssl_certificate /etc/letsencrypt/live/jansethu.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jansethu.example.com/privkey.pem;

    # Frontend PWA static files
    location / {
        root /var/www/jansethu/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API & Webhooks
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📞 Step 5: Telephony & SMS Provider Webhook Registration

Configure public webhook endpoints in your provider portal (Twilio / Exotel):

1. **Incoming Voice Call**: `POST https://jansethu.example.com/api/v1/telephony/webhooks/incoming`
2. **DTMF Keypress Collector**: `POST https://jansethu.example.com/api/v1/telephony/webhooks/dtmf`
3. **Voice Audio Collector**: `POST https://jansethu.example.com/api/v1/telephony/webhooks/voice`
4. **SMS Delivery Callback**: `POST https://jansethu.example.com/api/v1/sms/webhooks/status`

Ensure custom header `X-Webhook-Secret` matches your configured `WEBHOOK_SECRET`.

---

## 🧪 Step 6: Post-Deployment Smoke Test Checklist

- [ ] `GET https://jansethu.example.com/api/v1/health` returns `status: "ok"`.
- [ ] `GET https://jansethu.example.com/api/v1/health/ready` returns `status: "ready"`.
- [ ] `GET https://jansethu.example.com/api/v1/health/live` returns `status: "alive"`.
- [ ] Verify PWA loads over HTTPS without mixed-content errors.
- [ ] Register customer, login, search facility, and book appointment.
- [ ] Verify Provider console OPD queue loads and updates status.
- [ ] Verify Admin console telemetry monitoring displays active calls and SMS logs.
