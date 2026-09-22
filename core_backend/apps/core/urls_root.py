# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
from django.http import Http404, HttpResponse
from django.urls import path

from . import views


def privacy_view(request):
    """Aviso LFPDPPP estático (URL pública para Data Safety del APK).

    Sirve el archivo sin motor de templates a propósito: es contenido legal
    100% estático y evita acoplar compliance al render de Django.
    """
    from pathlib import Path

    from django.conf import settings
    page = Path(settings.BASE_DIR) / "templates" / "privacy.html"
    if not page.is_file():
        raise Http404()
    return HttpResponse(page.read_text(encoding="utf-8"),
                        content_type="text/html; charset=utf-8")


urlpatterns = [
    path('', views.index_view, name='index'),
    # Aviso de privacidad LFPDPPP (URL pública para Data Safety del APK).
    path('privacy/', privacy_view, name='privacy'),
]
