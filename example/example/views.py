from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def index(request: HttpRequest) -> HttpResponse:
    # Inner import to test that changes to this file are also detected.
    from example import fruits

    return render(
        request,
        "index.html",
        {
            "title": "Incredible citrus fruits.",
            "fruits": fruits.get_citrus_fruits(),
        },
    )


@require_GET
def favicon(request: HttpRequest) -> HttpResponse:
    return HttpResponse(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            + '<text y=".9em" font-size="90">👀</text>'
            + "</svg>"
        ),
        content_type="image/svg+xml",
    )
