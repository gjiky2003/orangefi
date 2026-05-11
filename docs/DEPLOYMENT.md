# OrangeFi — Deployment Guide

This guide covers local development setup, staging deployment on Render, and the production AWS architecture target.

---

## Prerequisites

### Local Development

| Tool | Version | Purpose |
|------|---------|---------|
| **Docker Desktop** | 24+ | Container runtime |
| **Docker Compose** | v2.24+ | Multi-service orchestration |
| **Node.js** | 18+ | Frontend development (outside Docker) |
| **Python** | 3.12+ | Backend development (outside Docker) |
| **Git** | 2.x | Version control |

### Cloud Deployment

| Service | Account Required | Purpose |
|---------|-----------------|---------|
| **GitHub** | Free | Source control + CI/CD |
| **Render** | Free-tier | MVP/Staging hosting |
| **AWS** | Production only | Production infrastructure |
| **Docker Hub** | Free | Container registry |

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/orangefi/orangefi.git
cd orangefi
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your development values. The defaults work for local Docker development.

### 3. Start Infrastructure Services

```bash
docker compose -f infrastructure/docker-compose.yml up -d postgres redis minio
```

This starts:
- **PostgreSQL 16** — Primary database (`localhost:5432`)
- **Redis 7** — Cache and job queue (`localhost:6379`)
- **MinIO** — S3-compatible object storage (`localhost:9000`, console: `localhost:9001`)
- **MinIO Init** — Creates required buckets (`orangefi-documents`, `orangefi-public`)

### 4. Start the Backend

```bash
docker compose -f infrastructure/docker-compose.yml up -d backend
```

The backend is available at `http://localhost:8000`.

### 5. Start the Frontend

```bash
docker compose -f infrastructure/docker-compose.yml up -d frontend
```

The frontend is available at `http://localhost:3000`.

### 6. Seed the Database

```bash
docker compose -f infrastructure/docker-compose.yml exec backend python scripts/seed.py
```

This creates:
- **50 borrowers** — Synthetic borrower profiles with varied credit profiles
- **120 applications** — Across all application statuses
- **30 funded loans** — With full payment schedules
- **1 admin user** — `admin@orangefi.com` / `Admin123!`

### 7. Verify Installation

```bash
# Health check
curl http://localhost:8000/api/health

# Open browser
open http://localhost:3000
```

### Full Startup (Single Command)

```bash
docker compose -f infrastructure/docker-compose.yml up -d
```

### Stop Everything

```bash
docker compose -f infrastructure/docker-compose.yml down
```

To stop and **delete all data** (volumes):
```bash
docker compose -f infrastructure/docker-compose.yml down -v
```

### Useful Docker Commands

```bash
# Tail backend logs
docker compose -f infrastructure/docker-compose.yml logs -f backend

# Tail frontend logs
docker compose -f infrastructure/docker-compose.yml logs -f frontend

# Run a command inside the backend container
docker compose -f infrastructure/docker-compose.yml exec backend bash

# Access PostgreSQL
docker compose -f infrastructure/docker-compose.yml exec postgres psql -U orangefi -d orangefi

# Access Redis CLI
docker compose -f infrastructure/docker-compose.yml exec redis redis-cli

# Rebuild a service (after dependency changes)
docker compose -f infrastructure/docker-compose.yml build backend --no-cache
```

---

## Render Deployment (Staging)

Render is the recommended platform for MVP/staging hosting with generous free tiers.

### Step 1: Prepare Your Repository

Ensure your GitHub repository contains the full project. Render will deploy directly from GitHub branches.

### Step 2: Create a PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name:** `orangefi-db`
   - **Database:** `orangefi`
   - **User:** `orangefi`
   - **Region:** `US East` (or closest to your users)
   - **Plan:** Free (or Starter for $7/mo)
4. Click **Create Database**
5. Copy the **Internal Database URL** and **Password** for the next step

### Step 3: Create the Backend Web Service

1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `orangefi-backend`
   - **Runtime:** Docker
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Dockerfile Path:** `Dockerfile`
   - **Instance Type:** Free
4. Add Environment Variables (see table below)
5. Click **Create Web Service**

### Step 4: Create the Frontend Web Service

1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `orangefi-frontend`
   - **Runtime:** Docker
   - **Branch:** `main`
   - **Root Directory:** `frontend`
   - **Dockerfile Path:** `Dockerfile`
   - **Instance Type:** Free
4. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL`: `https://orangefi-backend.onrender.com/api/v1`
   - `NEXT_PUBLIC_APP_NAME`: `OrangeFi`
   - `NEXT_PUBLIC_ENVIRONMENT`: `staging`
5. Click **Create Web Service**

### Step 5: Verify Deployment

1. Wait for both services to show **Live** status (3-5 minutes)
2. Check backend health: `https://orangefi-backend.onrender.com/api/health`
3. Open frontend: `https://orangefi-frontend.onrender.com`
4. Run seed data:

```bash
curl -X POST https://orangefi-backend.onrender.com/api/v1/seed -H "Content-Type: application/json"
```

### Custom Domain (Optional)

1. Go to your Render service → **Settings** → **Custom Domain**
2. Add your domain (e.g., `api.orangefi.com`)
3. Update your DNS provider with the CNAME record provided by Render
4. Configure SSL (automatic with Render)

### Render Environment Variables

#### Backend

| Variable | Value | Notes |
|----------|-------|-------|
| `APP_NAME` | `OrangeFi` | |
| `APP_VERSION` | `0.1.0` | |
| `ENVIRONMENT` | `staging` | |
| `DEBUG` | `false` | Don't enable in staging |
| `SECRET_KEY` | `<generate-strong-key>` | At least 32 chars, use `openssl rand -hex 32` |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Use Render Internal Database URL |
| `DATABASE_URL_SYNC` | `postgresql+psycopg2://...` | Same URL, different driver |
| `REDIS_URL` | `redis://...` | Optional in staging |
| `CORS_ORIGINS` | `https://orangefi-frontend.onrender.com` | |
| `ADMIN_EMAIL` | `admin@orangefi.com` | Change this |
| `ADMIN_PASSWORD` | `<strong-password>` | Change this |
| `ENCRYPTION_KEY` | `<32-byte-hex-key>` | `openssl rand -hex 32` |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | |
| `RATE_LIMIT_PER_MINUTE` | `120` | |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `10` | |
| `SENTRY_DSN` | `<your-sentry-dsn>` | Optional |
| `PLAID_ENV` | `sandbox` | Leave as sandbox |
| `STRIPE_SECRET_KEY` | `<stripe-test-key>` | Use test keys |
| `SENDGRID_API_KEY` | `<sendgrid-key>` | Optional |
| `TWILIO_ACCOUNT_SID` | `<twilio-sid>` | Optional |

#### Frontend

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://orangefi-backend.onrender.com/api/v1` |
| `NEXT_PUBLIC_APP_NAME` | `OrangeFi` |
| `NEXT_PUBLIC_ENVIRONMENT` | `staging` |

---

## AWS Production Target

The production architecture uses AWS managed services for scalability, reliability, and security.

### Architecture Components

| Component | AWS Service | Configuration |
|-----------|-------------|--------------|
| **Compute (Backend)** | ECS Fargate | 2+ tasks, auto-scaling (2-10), 2 vCPU / 4GB RAM each |
| **Compute (Frontend)** | ECS Fargate | 2+ tasks, auto-scaling (2-6), 1 vCPU / 2GB RAM each |
| **Database** | RDS PostgreSQL 16 | db.r6g.large (2 vCPU, 16GB RAM), Multi-AZ, automated backups |
| **Cache** | ElastiCache Redis 7 | cache.r6g.large, cluster mode disabled, 1 replica |
| **Storage** | S3 Standard | `orangefi-documents` (private), `orangefi-public` (downloadable) |
| **CDN** | CloudFront | Frontend distribution, S3 origin for static assets |
| **Load Balancer** | ALB | Application Load Balancer, HTTPS listener, WAF integration |
| **Secrets** | AWS Secrets Manager | ENCRYPTION_KEY, SECRET_KEY, API keys |
| **Monitoring** | CloudWatch | Logs, metrics, dashboards, alarms |
| **Email** | Amazon SES | Transactional emails (alternative to SendGrid) |
| **CI/CD** | CodePipeline | ECR → ECS blue/green deployments |

### Deployment Steps (AWS)

#### 1. Infrastructure Setup

```bash
# Prerequisites: AWS CLI configured, Terraform installed
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply
terraform apply tfplan
```

#### 2. ECR Repositories

```bash
# Create repositories
aws ecr create-repository --repository-name orangefi/backend
aws ecr create-repository --repository-name orangefi/frontend

# Build and push backend
cd backend
docker build -t orangefi/backend .
docker tag orangefi/backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/orangefi/backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/orangefi/backend:latest

# Build and push frontend
cd ../frontend
docker build -t orangefi/frontend .
docker tag orangefi/frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/orangefi/frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/orangefi/frontend:latest
```

#### 3. ECS Task Definitions

Create task definitions for backend and frontend with the environment variables from the reference table below. Use AWS Secrets Manager for sensitive values.

#### 4. RDS Setup

```bash
# Create PostgreSQL instance
aws rds create-db-instance \
    --db-instance-identifier orangefi-prod \
    --db-instance-class db.r6g.large \
    --engine postgres \
    --engine-version 16 \
    --master-username orangefi \
    --master-user-password <generate-secure> \
    --allocated-storage 100 \
    --storage-type gp3 \
    --multi-az \
    --backup-retention-period 30 \
    --deletion-protection
```

#### 5. ElastiCache Setup

```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id orangefi-redis \
    --cache-node-type cache.r6g.large \
    --engine redis \
    --engine-version 7.0 \
    --num-cache-nodes 2 \
    --az-mode cross-az
```

#### 6. Configure Security Groups

- **ALB:** Inbound 443 (HTTPS) from 0.0.0.0/0
- **ECS Backend:** Inbound 8000 from ALB security group
- **ECS Frontend:** Inbound 3000 from ALB security group
- **RDS:** Inbound 5432 from ECS backend security group
- **ElastiCache:** Inbound 6379 from ECS backend security group
- **S3:** VPC Endpoint for private subnet access

#### 7. Configure CloudFront

- Origin 1: ALB (frontend)
- Origin 2: S3 bucket (static assets)
- Behaviors: Default (*) → ALB, /static/* → S3
- SSL: Amazon certificate (us-east-1)
- WAF: Rate limiting, SQL injection protection, XSS protection

#### 8. DNS Configuration

```
orangefi.com         → CloudFront (frontend)
api.orangefi.com     → ALB (backend)
cdn.orangefi.com     → CloudFront (assets)
```

---

## CI/CD Pipeline (GitHub Actions)

The project is set up for GitHub Actions CI/CD. Create the following workflow files.

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Lint
        run: |
          cd backend
          pip install ruff
          ruff check app/
      - name: Test
        run: |
          cd backend
          pip install pytest pytest-asyncio
          pytest -x -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Lint
        run: |
          cd frontend
          npm run lint
      - name: Typecheck
        run: |
          cd frontend
          npm run typecheck
      - name: Build
        run: |
          cd frontend
          npm run build
```

### `.github/workflows/deploy.yml`

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy Backend
        run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK_BACKEND }}
      - name: Deploy Frontend
        run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK_FRONTEND }}
```

### Render Deploy Hooks

1. Go to each Render service → **Settings** → **Deploy Hooks**
2. Create a deploy hook for each service
3. Add the hook URLs as GitHub secrets: `RENDER_DEPLOY_HOOK_BACKEND` and `RENDER_DEPLOY_HOOK_FRONTEND`

---

## Monitoring Setup

### Sentry Error Tracking

```python
# Configure in app/config.py
SENTRY_DSN = os.getenv("SENTRY_DSN")

# Initialize in app/main.py
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.2,  # 20% in production
    send_default_pii=False,  # Never send PII to Sentry
)
```

### Prometheus Metrics

The backend exposes Prometheus metrics at `/api/metrics`:

```
# python_info{version="3.12.0"}
# http_requests_total{method="GET",path="/api/health"} 42
# http_request_duration_seconds{method="POST",path="/api/v1/underwriting/score"} 0.145
```

### Health Checks

Both Docker Compose and production deployments include health checks:

```dockerfile
# Backend Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1
```

### Structured Logging

All backend logs are structured with consistent fields:

```
2026-05-11 14:00:00,000 | INFO | orangefi.underwriting.scorer | RiskScorer model weights loaded from ./app/underwriting/models/model_weights.json
2026-05-11 14:00:01,000 | INFO | orangefi.underwriting.decision | Application UW-2026-00123 scored at Stage 2: risk_score=28, cash_flow_adjusted=false
2026-05-11 14:00:02,000 | WARNING | orangefi | Slow request: POST /api/v1/underwriting/score took 1.423s
```

---

## Environment Variables Reference

### Application Core

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | `OrangeFi` | Application display name |
| `APP_VERSION` | No | `0.1.0` | Semantic version |
| `ENVIRONMENT` | No | `development` | `development`, `staging`, or `production` |
| `DEBUG` | No | `false` | Enable debug mode (stack traces, detailed errors) |
| `SECRET_KEY` | **Yes** | — | JWT signing key (min 32 characters, use `openssl rand -hex 32`) |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated allowed origins |
| `SENTRY_DSN` | No | — | Sentry error tracking DSN |

### Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | **Yes** | — | Async connection string: `postgresql+asyncpg://user:pass@host:5432/db` |
| `DATABASE_URL_SYNC` | **Yes** | — | Sync connection string: `postgresql+psycopg2://user:pass@host:5432/db` |
| `DB_ECHO` | No | `false` | Log all SQL queries (development only) |

### Redis

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection string |
| `CELERY_BROKER_URL` | No | `redis://localhost:6379/1` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | No | `redis://localhost:6379/1` | Celery result backend |

### Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `30` | Refresh token TTL in days |
| `MFA_ISSUER_NAME` | No | `OrangeFi` | TOTP issuer name displayed in authenticator apps |
| `ADMIN_EMAIL` | No | `admin@orangefi.com` | Default admin account email |
| `ADMIN_PASSWORD` | **Yes** | — | Default admin account password |

### Encryption

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENCRYPTION_KEY` | **Yes** | — | AES-256 key (64 hex chars = 32 bytes), generate with `openssl rand -hex 32` |

### Rate Limiting

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RATE_LIMIT_PER_MINUTE` | No | `60` | General API rate limit per IP |
| `RATE_LIMIT_AUTH_PER_MINUTE` | No | `5` | Auth endpoint rate limit per IP |

### Plaid (Bank Linking)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PLAID_CLIENT_ID` | For Plaid | — | Plaid API client ID |
| `PLAID_SECRET` | For Plaid | — | Plaid API secret |
| `PLAID_ENV` | No | `sandbox` | `sandbox`, `development`, or `production` |

### Stripe (Payments)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STRIPE_SECRET_KEY` | For Stripe | — | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | For webhooks | — | Stripe webhook signing secret |
| `STRIPE_PUBLISHABLE_KEY` | For frontend | — | Stripe publishable key |

### Twilio (SMS)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TWILIO_ACCOUNT_SID` | For SMS | — | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | For SMS | — | Twilio auth token |
| `TWILIO_FROM_NUMBER` | For SMS | — | Twilio phone number (E.164 format) |

### SendGrid (Email)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENDGRID_API_KEY` | For Email | — | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | No | `noreply@orangefi.com` | Sender email address |

### DocuSign (E-Signatures)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOCUSIGN_ACCOUNT_ID` | For DocuSign | — | DocuSign account ID |
| `DOCUSIGN_CLIENT_ID` | For DocuSign | — | DocuSign integration key |
| `DOCUSIGN_CLIENT_SECRET` | For DocuSign | — | DocuSign secret key |
| `DOCUSIGN_AUTH_SERVER` | No | `account-d.docusign.com` | `account-d.docusign.com` (dev) or `account.docusign.com` (prod) |

### Object Storage (S3/MinIO)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `S3_ENDPOINT` | For MinIO | — | MinIO endpoint (e.g., `http://localhost:9000`). Leave empty for AWS S3. |
| `S3_ACCESS_KEY` | **Yes** | — | S3 access key or MinIO username |
| `S3_SECRET_KEY` | **Yes** | — | S3 secret key or MinIO password |
| `S3_BUCKET` | No | `orangefi-documents` | S3 bucket for document storage |
| `S3_REGION` | No | `us-east-1` | AWS region |

### Credit Bureau

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CREDIT_BUREAU_API_KEY` | For Bureau | — | Credit bureau API key |
| `CREDIT_BUREAU_BASE_URL` | No | `https://api.mockbureau.com/v1` | Bureau API base URL |

### Model Directory

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MODEL_DIR` | No | `./app/underwriting/models` | Path to ML model weight files |

### Celery

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CELERY_BROKER_URL` | For Celery | `redis://localhost:6379/1` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | For Celery | `redis://localhost:6379/1` | Celery result backend |

### Monitoring

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | No | `/tmp` | Directory for Prometheus multiprocess metrics |
| `SENTRY_DSN` | No | — | Sentry error tracking DSN |
| `SENTRY_ENVIRONMENT` | No | Same as `ENVIRONMENT` | Sentry environment tag |

---

## Security Checklist for Production

- [ ] `SECRET_KEY` is a strong, unique value (min 32 chars, not in version control)
- [ ] `ENCRYPTION_KEY` is a 64-character hex string stored in AWS Secrets Manager
- [ ] `ADMIN_PASSWORD` is a strong password (not the default)
- [ ] `DEBUG` is set to `false`
- [ ] `CORS_ORIGINS` is restricted to known domains
- [ ] Database passwords are unique and stored in Secrets Manager
- [ ] TLS/SSL is enforced (HTTPS-only)
- [ ] API rate limiting is configured appropriately
- [ ] S3 buckets are not publicly accessible (except `/orangefi-public`)
- [ ] RDS encryption at rest is enabled
- [ ] Automated backups are configured (30-day retention)
- [ ] Multi-AZ deployment for RDS and ElastiCache
- [ ] WAF rules are configured on the ALB
- [ ] CloudFront with HTTPS-only and security headers
- [ ] VPC with private subnets for databases and cache
- [ ] Security group rules follow least-privilege principle
- [ ] Sentry is configured with `send_default_pii=False`
- [ ] Audit logging is enabled and logs are retained
