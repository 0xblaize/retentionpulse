from __future__ import annotations

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
load_dotenv(BASE_DIR.parent / ".env")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "retentionpulse-local-secret-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
configured_allowed_hosts = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",") if host.strip()]
render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS = [*configured_allowed_hosts, "testserver", *([render_hostname] if render_hostname else [])]
ROOT_URLCONF = "config.urls"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
INSTALLED_APPS = ["corsheaders", "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "web"]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "web" / "templates", FRONTEND_DIR / "dist"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.request",
            "django.contrib.messages.context_processors.messages",
        ]},
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
database_url = os.getenv("DATABASE_URL")
if not DEBUG and not database_url:
    raise ImproperlyConfigured("DATABASE_URL must be configured in production so sessions and passkeys survive deployments.")

DATABASES = {
    "default": dj_database_url.parse(
        database_url or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
STATIC_URL = "/static/"
STATICFILES_DIRS = [path for path in (BASE_DIR / "web" / "static", FRONTEND_DIR / "dist") if path.exists()]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("RETENTIONPULSE_MAX_UPLOAD_BYTES", str(250 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE
def _service_url(value: str, default: str) -> str:
    value = value.strip() or default
    return value if "://" in value else f"https://{value}"


RETENTIONPULSE_API_URL = _service_url(os.getenv("RETENTIONPULSE_API_URL", ""), "http://127.0.0.1:8001")
RETENTIONPULSE_DEMO_MODE = False
RETENTIONPULSE_RP_ID = os.getenv("RETENTIONPULSE_RP_ID") or "127.0.0.1"
RETENTIONPULSE_ORIGIN = _service_url(os.getenv("RETENTIONPULSE_ORIGIN", ""), "http://127.0.0.1:8000")
RETENTIONPULSE_RP_NAME = os.getenv("RETENTIONPULSE_RP_NAME", "RetentionPulse")
RETENTIONPULSE_WEBAUTHN_TIMEOUT_MS = int(os.getenv("RETENTIONPULSE_WEBAUTHN_TIMEOUT_MS", "60000"))
RETENTIONPULSE_FRONTEND_URL = os.getenv("RETENTIONPULSE_FRONTEND_URL", "http://127.0.0.1:5173").rstrip("/")
CORS_ALLOWED_ORIGINS = [origin.rstrip("/") for origin in os.getenv("CORS_ALLOWED_ORIGINS", RETENTIONPULSE_FRONTEND_URL).split(",") if origin]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [origin.rstrip("/") for origin in os.getenv("CSRF_TRUSTED_ORIGINS", f"{RETENTIONPULSE_ORIGIN},{RETENTIONPULSE_FRONTEND_URL}").split(",") if origin]
if RETENTIONPULSE_FRONTEND_URL.startswith("https://"):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SAMESITE = "None"
