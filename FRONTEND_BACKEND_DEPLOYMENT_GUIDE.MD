# FRONTEND_BACKEND_DEPLOYMENT_GUIDE.MD

This guide walks you through deploying a Django backend (Railway + PostgreSQL) and a frontend (Vercel). It’s designed for small-to-medium scale apps that need a reliable, low-ops setup with a clean separation of frontend and backend.

## Table of Contents

1. Prerequisites
2. Backend (Django) on Railway
   - 2.1 Prepare Django for production
   - 2.2 Configure environment variables
   - 2.3 Deploy on Railway
   - 2.4 Post-deploy checks
3. Frontend on Vercel
   - 3.1 Prepare frontend for production
   - 3.2 Deploy on Vercel
4. Connect Frontend and Backend
5. Optional Enhancements
6. Troubleshooting

---

## 1) Prerequisites

- GitHub account (both Railway and Vercel link to GitHub)
- Railway account (`https://railway.app`)
- Vercel account (`https://vercel.com`)
- Django app ready to deploy (this repository)
- Frontend app ready to deploy (e.g., React/Next.js)

---

## 2) Backend (Django) on Railway

### 2.1 Prepare Django for production

1) Install production dependencies locally and pin them to `requirements.txt`:

```bash
pip install gunicorn whitenoise django-cors-headers psycopg2-binary dj-database-url
pip freeze > requirements.txt
```

2) Update `config/settings.py` for a 12-factor, production-friendly setup:

```python
import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-dev-key")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Allow Railway and your custom domains
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".up.railway.app",  # any Railway subdomain
    "api.yourdomain.com",  # your custom API domain (optional)
]

# CSRF trusted origins must include scheme
CSRF_TRUSTED_ORIGINS = [
    "https://*.up.railway.app",
    "https://api.yourdomain.com",
    "https://your-frontend.vercel.app",
    "https://your-frontend-domain.com",
]

# Database (Railway will provide DATABASE_URL)
DATABASES = {
    "default": dj_database_url.config(  # type: ignore
        default=os.environ.get("DATABASE_URL", "sqlite:///" + str(BASE_DIR / "db.sqlite3")),
        conn_max_age=600,
    )
}

# Static files via WhiteNoise
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

INSTALLED_APPS = [
    # ... your existing apps ...
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    # ... the rest of your middleware ...
]

# CORS configuration (adjust to your frontend domains)
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.vercel.app",
    "https://your-frontend-domain.com",
]
CORS_ALLOW_CREDENTIALS = True  # if using cookie-based auth/sessions

# Security & proxy headers (important behind Railway proxy)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
# If your frontend is on a different domain and you use session cookie auth
SESSION_COOKIE_SAMESITE = "None"

# Recommended additional hardening for production
SECURE_HSTS_SECONDS = 3600  # increase gradually after verifying HTTPS
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
```

3) Optional: add a simple health check route to `config/urls.py` so Railway can probe readiness:

```python
from django.http import HttpResponse
from django.urls import path, include

def healthz(_request):
    return HttpResponse("ok")

urlpatterns = [
    # ... your URLs ...
    path("healthz", healthz),
]
```

4) Collect and commit static assets (WhiteNoise will serve them):

```bash
python manage.py collectstatic --noinput
```

5) Commit and push the changes:

```bash
git add -A
git commit -m "chore: production settings for Railway deployment"
git push
```

### 2.2 Configure environment variables

You will set these in Railway → Project → Variables. At minimum:

- `SECRET_KEY` = a long random string
- `DJANGO_SETTINGS_MODULE` = `config.settings`
- `DEBUG` = `false`
- `DATABASE_URL` = provided automatically when you add the PostgreSQL plugin

If you use custom domains, ensure they are reflected in `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

### 2.3 Deploy on Railway

1) Create a new Railway project and link your GitHub repo.

2) Add a PostgreSQL plugin to the project. Railway will inject `DATABASE_URL`.

3) Configure the start command (Service → Settings → Start Command):

```bash
python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 60
```

4) Trigger a deploy (push to your default branch or click Deploy). Watch the build and runtime logs.

5) After the service is running, open the public URL. You should see your app (or your root route behavior).

### 2.4 Post-deploy checks

- Run database migrations were applied (the start command handles this). If needed, run manually from Railway shell:

```bash
python manage.py migrate
```

- Create an admin user (first-time setup):

```bash
python manage.py createsuperuser
```

- Static files are being served by WhiteNoise (check your browser devtools → Network for `/static/...`).

- Optional: attach a custom domain in Railway and add it to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

---

## 3) Frontend on Vercel

### 3.1 Prepare frontend for production

- Ensure the frontend reads the API base URL from an environment variable, e.g. `NEXT_PUBLIC_API_URL`.
- For cookie-based sessions with Django, make sure your requests include credentials.

Example (Next.js fetch):

```ts
const api = process.env.NEXT_PUBLIC_API_URL;

export async function getUser() {
  const res = await fetch(`${api}/api/user/`, {
    credentials: "include", // needed for session cookies
  });
  if (!res.ok) throw new Error("Failed to fetch user");
  return res.json();
}
```

### 3.2 Deploy on Vercel

1) Push your frontend repo to GitHub and import it into Vercel (New Project → Import Git Repository).

2) Configure build settings if needed (Vercel usually auto-detects Next.js/React).

3) Add environment variables in Vercel → Settings → Environment Variables:

- `NEXT_PUBLIC_API_URL` = `https://<your-railway-service>.up.railway.app` (or your custom API domain)

4) Deploy. After deploy, you’ll get a vercel.app URL. Add it to your backend CORS/CSRF settings if not already present.

---

## 4) Connect Frontend and Backend

1) CORS and CSRF on Django must explicitly allow your frontend domain(s):

```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.vercel.app",
    "https://your-frontend-domain.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://your-frontend.vercel.app",
    "https://your-frontend-domain.com",
    "https://*.up.railway.app",
]

CORS_ALLOW_CREDENTIALS = True  # if using session cookies
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

2) In the frontend, send cookies if you rely on Django sessions:

```ts
fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/...`, { credentials: "include" })
```

3) If you use token/JWT auth instead of session cookies, you can keep `CORS_ALLOW_CREDENTIALS = False` and omit SameSite changes. Send tokens via `Authorization: Bearer <token>` headers.

---

## 5) Optional Enhancements

- Custom domains: point `api.yourdomain.com` to Railway; add to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Health checks: set Railway healthcheck path to `/healthz`.
- Backups: enable Railway Postgres backups or use external backup tooling.
- Monitoring/logging: use Railway logs and Vercel analytics; consider Sentry for error tracking.
- HTTPS/security: keep `DEBUG=False`, review `python manage.py check --deploy`, gradually increase HSTS.
- ASGI/websockets: if you adopt websockets later, run `uvicorn config.asgi:application` (Django ASGI) instead of Gunicorn WSGI, or use `gunicorn -k uvicorn.workers.UvicornWorker config.asgi:application`.

---

## 6) Troubleshooting

- DisallowedHost: add your Railway domain and custom domains to `ALLOWED_HOSTS`.
- 403 CSRF failures: ensure exact origins (with `https://`) in `CSRF_TRUSTED_ORIGINS`; include credentials and CSRF token on state-changing requests.
- CORS error: verify `CORS_ALLOWED_ORIGINS` matches your deployed frontend URL exactly (protocol + host).
- Static files 404: run `python manage.py collectstatic`; ensure WhiteNoise middleware is present and before common middleware.
- Database connection errors: confirm `DATABASE_URL` is set by Railway Postgres; ensure `psycopg2-binary` is installed.
- Mixed-content warnings: always use `https://` URLs for both frontend and backend.

---

## Quick Reference

- Railway start command:

```bash
python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 60
```

- Frontend env var on Vercel:

```bash
NEXT_PUBLIC_API_URL=https://<your-railway-service>.up.railway.app
```

By following these steps, you’ll have a production-ready Django backend on Railway and a frontend on Vercel, with proper CORS/CSRF, static file handling, and a clean deployment workflow.


