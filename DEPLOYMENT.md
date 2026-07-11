# Deployment Notes (Cloudflare-fronted)

Django apps can't run natively on Cloudflare Workers/Pages (those run V8
isolates, not a WSGI process) -- the standard, supported pattern is:
**Cloudflare in front (DNS + CDN/WAF/Tunnel) → your existing WSGI host behind
it** (a small VM, Fly.io, Railway, Render, etc., or `cloudflared tunnel` to a
box you already run). Everything below assumes that architecture.

## 1. Environment variables (set these on your host, never commit them)
| Variable | Example | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | (random 50+ chars) | required in production |
| `DJANGO_DEBUG` | `False` | |
| `DJANGO_ALLOWED_HOSTS` | `app.example.com,example.com` | |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://app.example.com` | must include scheme |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` | once Cloudflare SSL mode is Full/Full-Strict |
| `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` | from Google Cloud Console | |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | | use an app password, not your real one |

## 2. Cloudflare dashboard settings
- SSL/TLS mode: **Full (strict)** once your origin has a valid cert.
- Cache Rules: cache `/static/*` aggressively (the hashed filenames from
  `collectstatic` mean a changed file is a new URL, so long TTLs are safe).
  Do **not** cache `/api/*`, `/accounts/*`, or any authenticated page.
- Enable "Always Use HTTPS".

## 3. Release steps
```bash
pip install -r requirements.txt --break-system-packages
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn GenTech.wsgi:application --bind 0.0.0.0:8000
```

## 4. Google OAuth
Create OAuth credentials at https://console.cloud.google.com/apis/credentials
with redirect URI `https://<your-domain>/accounts/google/login/callback/`,
then set `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET`. The app is
now configured entirely via `SOCIALACCOUNT_PROVIDERS` in settings.py (not
the admin-managed `SocialApp` DB table), so it works out of the box on a
fresh database with zero manual admin setup -- just the two env vars.
