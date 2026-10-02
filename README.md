# Auth API starter

Django REST Framework starter with email login, JWT access tokens, an httpOnly
refresh cookie, organisation onboarding, Docker, and GHCR image builds.

**Stack:** Django 5 · DRF · PostgreSQL 16 · Redis 7 · Celery · JWT · Railway · GHCR

Use this repository as a **GitHub template** (or clone it) for a new backend.
Rename the starter defaults — they are environment variables and compose names.

---

## Start a new project

1. Create a GitHub repo from this template (or clone and push to a new remote).
   The image name is always `ghcr.io/<owner>/<repo>`.
2. Copy `.env.example` to `.env` and set `PROJECT_NAME` to your product name.
3. Change local names if you do not want the `dev` defaults (table below).
4. Enable GitHub Actions. A push to `main` publishes `:dev`. A GitHub Release
   publishes `:latest` plus the version tag, then runs `railway redeploy`.
5. Set `RAILWAY_TOKEN` and `RAILWAY_SERVICE_ID` on **this** repo only when that
   repo has its own Railway service. Do not copy another project's Railway secrets.

| What | File / variable | Starter default |
|------|-----------------|-----------------|
| GHCR image | GitHub repo name (`IMAGE_NAME: ${{ github.repository }}`) | `ghcr.io/<owner>/<repo>` |
| Tags | workflows | `:dev` on `main`; `:latest` and `{{version}}` on a Release |
| Frontend compose image | `API_IMAGE` in `.env` next to `docker-compose.frontend-dev.yml` | `ghcr.io/<owner>/<repo>:dev` |
| Product name (Swagger, emails) | `PROJECT_NAME` | `API` |
| Postgres | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `dev` |
| Compose project | `name:` in compose files | `dev`, `frontend-dev`, `fullstack` |
| Postgres volume | compose `volumes:` | `dev_postgres_data` |
| Refresh cookie | `REFRESH_COOKIE_NAME` | `dev_refresh` |
| From-address | `DEFAULT_FROM_EMAIL` | `noreply@localhost` |
| Frontend origin | `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` |
| Optional JWT HMAC | `JWT_SIGNING_KEY` | falls back to `DJANGO_SECRET_KEY` |

Keep `POSTGRES_*` identical in `.env`, `.env.frontend.example` / `.env.api`, and
the compose `db` service.

Mark the GitHub repository as a **template** so new projects can use
**Use this template**.

---

## Quick Start (Development)

### 1. Clone & configure

```bash
git clone https://github.com/<owner>/<repo>.git
cd <repo>
cp .env.example .env
# Edit PROJECT_NAME and any other defaults you want to change
```

### 2. Start the stack

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/api/docs/ |
| Frontend guide | http://localhost:8000/api/docs/frontend/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| Django Admin | http://localhost:8000/admin/ |
| Mailpit | http://localhost:8025 |

### 3. Create a superuser

```bash
docker compose exec api python manage.py createsuperuser
```

Log in at `/admin/` and add an organisation. The central admin gets a welcome
email in Mailpit. They set a password at `POST /api/auth/password/set/`, then
log in at `POST /api/auth/login/`.

### 4. Run tests

```bash
docker compose exec api pytest
```

---

## Project Structure

```
├── config/                  # Django project package
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   └── urls.py
├── apps/
│   ├── users/               # Custom User + auth endpoints
│   ├── organizations/       # Org model + admin onboarding
│   ├── common/              # Mixins, OpenAPI helpers, frontend guide
│   └── healthcheck/         # /api/health/
├── tests/
├── docker/api/
├── requirements/
├── docker-compose.yml
├── docker-compose.frontend-dev.yml
├── docker-compose.react.yml
├── railway.json
└── .github/workflows/
```

---

## Environment Variables

See [`.env.example`](.env.example). Frontend developers use
[`.env.frontend.example`](.env.frontend.example).

### Required for all environments

| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key |
| `REDIS_URL` | Redis connection URL |

### Local Docker

| Variable | Description |
|---|---|
| `POSTGRES_DB` | Database name (default `dev`) |
| `POSTGRES_USER` | Database user (default `dev`) |
| `POSTGRES_PASSWORD` | Database password (default `dev`) |
| `POSTGRES_HOST` | `db` in Compose |
| `POSTGRES_PORT` | `5432` |

### Production (Railway)

Railway injects `DATABASE_URL` and `REDIS_URL`. Do not set `POSTGRES_*` there.

| Variable | Description |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_ALLOWED_HOSTS` | Railway domain + custom domain |
| `CORS_ALLOWED_ORIGINS` | Deployed frontend origin(s) |
| `DO_SPACES_*` | DigitalOcean Spaces for static/media |
| `EMAIL_HOST` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP |

---

## Celery

Workers and beat are in `docker-compose.yml`.

On Railway, deploy the same image as separate services:

- **Worker:** `celery -A config worker --loglevel=info --concurrency=2`
- **Beat:** `celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler`

---

## DigitalOcean Spaces (production)

1. Create a Spaces bucket
2. Set `DO_SPACES_*` on Railway
3. `collectstatic` uploads static files on deploy

---

## Deployment (Railway)

### One-time setup

1. Create a Railway project and add **Postgres** and **Redis**
2. Add a service → **Deploy from image** → `ghcr.io/<owner>/<repo>:latest`
3. Set production env vars
4. Add GitHub secrets `RAILWAY_TOKEN` and `RAILWAY_SERVICE_ID` on this repo

### Releasing

Publish a GitHub Release (tag `v1.2.0`). Actions will:

1. Build the prod image
2. Push `ghcr.io/<owner>/<repo>:1.2.0` and `:latest`
3. Run migrations against a fresh Postgres
4. `railway redeploy` for this repo's service

A merge to `main` pushes `ghcr.io/<owner>/<repo>:dev` for frontend compose.

---

## Auth

Login is **email + password**. Access token in JSON; refresh token in an httpOnly
cookie. See [FRONTEND_API.md](FRONTEND_API.md) and `/api/docs/frontend/`.

---

## Running Tests

```bash
docker compose exec api pytest

# Locally (venv + Postgres + Redis)
pip install -r requirements/development.txt
pytest
```

---

## Adding a New App

```bash
docker compose exec api python manage.py startapp myapp apps/myapp
```

Add `"apps.myapp"` to `LOCAL_APPS` in `config/settings/base.py`.
