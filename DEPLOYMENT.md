# JanSethu AI — Production Deployment Guide

This guide outlines step-by-step instructions for deploying JanSethu AI to cloud infrastructure (Render, Railway, AWS, Azure, GCP, or Docker containers) in PostgreSQL production mode.

---

## 1. Prerequisites

- Python 3.10+ runtime environment (or Docker container engine).
- Node.js 18+ runtime environment (for building React frontend).
- PostgreSQL 14+ database instance.
- Configured environment variables (see `.env.example`).

---

## 2. Deployment Architecture

```
   [ User Browser / Phone ]
              │
              ▼
   [ NGINX / Cloudflare / HTTPS Ingress ]
        │                       │
        ▼                       ▼
  [ React PWA ]       [ FastAPI Backend (Uvicorn) ]
  (Static Build)                 │
                                 ├──► [ PostgreSQL Database ]
                                 ├──► [ Telephony Webhook APIs ]
                                 └──► [ SMS / STT / TTS Adapters ]
```

---

## 3. Step-by-Step Backend Deployment

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/jansethu-ai/jansethu-ai.git
cd jansethu-ai/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Create a production `.env` file in `backend/` or set environment variables in your cloud provider's dashboard:

```env
APP_ENV=production
DEBUG=false
SECRET_KEY=your_64_byte_random_production_secret_key
DATABASE_URL=postgresql://user:password@pg-host:5432/jansethudb
PUBLIC_BASE_URL=https://api.jansethu.example.com
CORS_ORIGINS=https://jansethu.example.com
TELEPHONY_PROVIDER=twilio  # Or exotel / vonage / development
STT_PROVIDER=mock
TTS_PROVIDER=mock
SMS_PROVIDER=msg91        # Or twilio / development
LOCATION_PROVIDER=mock
LLM_PROVIDER=development
```

### Step 3: Run Database Migrations
Apply Alembic database migrations to create relational database schema on PostgreSQL:
```bash
alembic upgrade head
```

### Step 4: Validate Production Configuration
Execute the configuration audit tool to verify database and secret readiness:
```bash
python -m app.config.check_config
```

### Step 5: Launch Production ASGI Server
Start the Uvicorn ASGI server with production worker pool:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 4. Frontend Deployment (PWA)

### Step 1: Install Dependencies & Build Production Assets
```bash
cd jansethu-ai/frontend
npm install
VITE_API_BASE_URL=https://api.jansethu.example.com/api/v1 npm run build
```

### Step 2: Host Static Build
Deploy the generated `frontend/dist/` directory to Vercel, Netlify, Cloudflare Pages, AWS S3 + CloudFront, or NGINX.

---

## 5. Docker Container Deployment

A pre-built `Dockerfile` is provided in `backend/`:

```bash
cd backend
docker build -t jansethu-backend:v2.0 .
docker run -d -p 8000:8000 --env-file .env jansethu-backend:v2.0
```

---

## 6. Health Monitoring & Observability

Monitor deployment readiness using standardized endpoints:
- Liveness: `GET https://api.jansethu.example.com/health/live`
- Readiness: `GET https://api.jansethu.example.com/health/ready`
- Comprehensive Status: `GET https://api.jansethu.example.com/api/v1/health`
