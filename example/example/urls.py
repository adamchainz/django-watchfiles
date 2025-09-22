from __future__ import annotations

from django.urls import path

from example import views

urlpatterns = [
    path("", views.index),
    path("favicon.ico", views.favicon),
]
