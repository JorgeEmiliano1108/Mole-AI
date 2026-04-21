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
Authentication middleware for Mole.AI.

Contains:
  • JwtAuthMiddleware  — WebSocket (Django Channels) JWT auth via query string.
  • JwtHttpMiddleware  — HTTP request JWT validation for IoT ingest endpoints.
"""
import json
import logging

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from channels.db import database_sync_to_async
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

# ── Protected IoT paths that require JWT Bearer ──────────────────────────────
_IOT_PROTECTED_PATHS = (
    "/api/v1/sensor-data/",
    "/api/v1/sensor-data/batch/",
    "/api/v1/sensors/ingest",
)


# =============================================================================
# WebSocket JWT Middleware (Django Channels — ASGI)
# =============================================================================

@database_sync_to_async
def get_user(token):
    try:
        from apps.authentication.jwks import get_verification_key
        
        # Auto-detect algorithm and get correct verification key
        verification_key, algorithms = get_verification_key(
            settings.SUPABASE_URL, token
        )
        
        payload = jwt.decode(
            token,
            verification_key,
            algorithms=algorithms,
            audience='authenticated',
            options={
                'verify_aud': True,
                'verify_exp': True,
            }
        )
        
        user_id = payload.get('sub')
        email = payload.get('email')
        
        if not user_id or not email:
            return AnonymousUser()
            
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=user_id,
            defaults={
                'email': email,
                'is_active': True,
            }
        )
        return user
    except Exception:
        return AnonymousUser()

class JwtAuthMiddleware:
    """
    Middleware to authenticate WebSocket connections using Supabase JWT
    passed in query string: ws://host/path/?token=<token>
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        try:
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            
            # Simple hygiene check
            if token and token not in ['null', 'undefined', '']:
                user = await get_user(token)
                scope['user'] = user
                # logger.info(f"WS Auth Success: {user}")
            else:
                scope['user'] = AnonymousUser()
                # logger.info("WS Auth: Anonymous (No token)")
                
        except Exception as e:
            # logger.error(f"WS Auth Error: {e}")
            scope['user'] = AnonymousUser()
            
        return await self.inner(scope, receive, send)


# =============================================================================
# HTTP JWT Middleware — Zero-Trust IoT Ingest Protection
# =============================================================================
# Intercepts POST requests to IoT ingest endpoints and enforces JWT Bearer
# validation against Supabase JWKS.  Coexists with HardwareAPIKeyAuthentication
# during the transition period: if a valid Bearer token is present it takes
# precedence; if absent, the request falls through to the legacy API-key flow.
# =============================================================================

class JwtHttpMiddleware:
    """
    Django HTTP middleware that enforces Supabase JWT validation on
    IoT sensor ingest endpoints.

    The middleware only activates for POST requests whose path starts with
    one of the entries in ``_IOT_PROTECTED_PATHS``.  For all other requests
    it is a transparent pass-through with zero overhead.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Fast path: only intercept POST on protected IoT routes
        if request.method == "POST" and any(
            request.path.startswith(p) for p in _IOT_PROTECTED_PATHS
        ):
            rejection = self._enforce_jwt(request)
            if rejection is not None:
                return rejection

        return self.get_response(request)

    # ── Internal helpers ─────────────────────────────────────────────────

    @staticmethod
    def _extract_bearer(request) -> str | None:
        """Return the raw JWT string from the Authorization header, or None."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header[7:].strip()
        return token if token else None

    def _enforce_jwt(self, request) -> JsonResponse | None:
        """Validate JWT and annotate request.  Returns a JsonResponse on failure."""
        token = self._extract_bearer(request)

        if token is None:
            # No Bearer header — let the request fall through to the legacy
            # HardwareAPIKeyAuthentication flow (backward compatibility).
            return None

        try:
            from apps.authentication.jwks import get_verification_key

            verification_key, algorithms = get_verification_key(
                settings.SUPABASE_URL, token
            )

            payload = jwt.decode(
                token,
                verification_key,
                algorithms=algorithms,
                audience="authenticated",
                options={"verify_aud": True, "verify_exp": True},
                leeway=getattr(settings, "SUPABASE_JWT_LEEWAY", 30),
            )

            sub = payload.get("sub")
            email = payload.get("email")

            if not sub or not email:
                logger.warning("JWT missing sub/email claims on IoT ingest")
                return JsonResponse(
                    {"error": "JWT payload missing required claims (sub, email)."},
                    status=401,
                )

            # Annotate request so downstream views can access the identity
            request.supabase_uid = sub
            request.supabase_email = email

            logger.debug(
                "IoT JWT validated: sub=%s path=%s", sub, request.path
            )
            return None  # allow through

        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT on IoT ingest path=%s", request.path)
            return JsonResponse(
                {"error": "Token has expired."}, status=401
            )
        except jwt.InvalidTokenError as exc:
            logger.warning(
                "Invalid JWT on IoT ingest path=%s: %s", request.path, exc
            )
            return JsonResponse(
                {"error": f"Invalid token: {exc}"}, status=401
            )
        except Exception as exc:
            logger.exception(
                "Unexpected error validating IoT JWT path=%s: %s",
                request.path,
                exc,
            )
            return JsonResponse(
                {"error": "Token validation error."}, status=401
            )
