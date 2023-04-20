from __future__ import annotations

from typing import Any

SECRET_KEY = "not-secret"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "LOCATION": ":memory:",
    }
}

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS: list[str] = []

STATIC_URL = "/static/"

TEMPLATES: list[dict[str, Any]] = []

USE_TZ = True
