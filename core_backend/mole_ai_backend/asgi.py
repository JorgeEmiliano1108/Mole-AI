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
"""
ASGI config for mole_ai_backend project.

Optimized configuration for Django Channels + WebSocket + Static Files.
"""

import os
import sys
import logging
from pathlib import Path

# Agregar el directorio apps al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / 'apps'))

# Establecer configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mole_ai_backend.settings')

import django
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from apps.authentication.middleware import JwtAuthMiddleware

# Importar routing con fallback mejorado
logger = logging.getLogger(__name__)
try:
    from apps.core.routing import websocket_urlpatterns
    logger.info("WebSocket routes loaded from apps.core.routing")
except ImportError as e:
    logger.warning(f"Error loading core.routing: {e}")
    websocket_urlpatterns = []

# Configuración ASGI con seguridad y manejo de errores
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JwtAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

# Configuración de logging para ASGI
import logging
logger = logging.getLogger(__name__)
logger.info("ASGI application configured with Django Channels")
logger.info(f"HTTP endpoint: http://0.0.0.0:8000/")
logger.info(f"WebSocket endpoint: ws://0.0.0.0:8000/ws/chat/")