from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "retentionpulse-local-secret-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",") if host]
ROOT_URLCONF = "config.urls"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "web"]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "web" / "templates", BASE_DIR / "frontend" / "dist"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.request",
            "django.contrib.messages.context_processors.messages",
        ]},
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "web" / "static", BASE_DIR / "frontend" / "dist"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("RETENTIONPULSE_MAX_UPLOAD_BYTES", str(250 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE
RETENTIONPULSE_API_URL = os.getenv("RETENTIONPULSE_API_URL", "http://127.0.0.1:8001")
RETENTIONPULSE_DEMO_MODE = False
RETENTIONPULSE_RP_ID = os.getenv("RETENTIONPULSE_RP_ID", "127.0.0.1")
RETENTIONPULSE_ORIGIN = os.getenv("RETENTIONPULSE_ORIGIN", "http://127.0.0.1:8000")
RETENTIONPULSE_RP_NAME = os.getenv("RETENTIONPULSE_RP_NAME", "RetentionPulse")
RETENTIONPULSE_WEBAUTHN_TIMEOUT_MS = int(os.getenv("RETENTIONPULSE_WEBAUTHN_TIMEOUT_MS", "60000"))
