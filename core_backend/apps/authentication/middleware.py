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
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from urllib.parse import parse_qs

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
