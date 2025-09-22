from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Hide development server warning
# https://docs.djangoproject.com/en/stable/ref/django-admin/#envvar-DJANGO_RUNSERVER_HIDE_WARNING
os.environ["DJANGO_RUNSERVER_HIDE_WARNING"] = "true"

# 1. Django Core Settings

# Dangerous: disable host header validation
ALLOWED_HOSTS = ["*"]

BASE_DIR = Path(__file__).resolve().parent

DATABASES: dict[str, dict[str, Any]] = {}

DEBUG = True

INSTALLED_APPS = [
    # Project
    "example",
    # Third Party
    "django_watchfiles",
    # Contrib
    "django.contrib.staticfiles",
]

ROOT_URLCONF = "example.urls"

SECRET_KEY = "django-insecure-WCglZv2CA4v59K24bXfADwNDXc3HlwDY"  # typos: ignore

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
    },
]

USE_TZ = True

# 2. Django Contrib Settings

# django.contrib.staticfiles

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_URL = "/static/"

# 3. Third party apps

# daphne

ASGI_APPLICATION = "example.asgi.app"
