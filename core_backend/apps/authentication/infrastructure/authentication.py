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
import hmac
import logging
import json

from rest_framework import authentication, exceptions
from django.conf import settings
import jwt
from jwt import (
    ExpiredSignatureError,
    InvalidTokenError,
    InvalidAudienceError,
    InvalidSignatureError,
    DecodeError,
    InvalidAlgorithmError,
)
from django.contrib.auth import get_user_model
from django.http import HttpRequest


class SupabaseAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for Supabase JWT tokens.
    
    Validates JWT tokens from Supabase and extracts user information.
    """
    
    def authenticate(self, request: HttpRequest):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = authentication.get_authorization_header(request).split()
        
        if not auth_header or auth_header[0].lower() != b'bearer':
            return None
            
        if len(auth_header) == 1:
            raise exceptions.AuthenticationFailed(
                'Invalid bearer header. No credentials provided.'
            )
        elif len(auth_header) > 2:
            raise exceptions.AuthenticationFailed(
                'Invalid bearer header. Token string should not contain spaces.'
            )
            
        try:
            token = auth_header[1].decode('utf-8')
        except UnicodeError:
            raise exceptions.AuthenticationFailed(
                'Invalid token header. Token string should not contain invalid characters.'
            )
            
        return self._authenticate_credentials(request, token)
    
    def _authenticate_credentials(self, request: HttpRequest, token: str):
        """
        Authenticate the token with Supabase JWT secret and return user.
        """
        is_local_superuser = False

        # Helper: mask token for safe logging (never log full token)
        def _mask_token(tok: str) -> str:
            try:
                if not tok or not isinstance(tok, str):
                    return ''
                if len(tok) <= 12:
                    # keep last 4 characters visible
                    return '*' * max(0, len(tok) - 4) + tok[-4:]
                return tok[:6] + '…' + tok[-6:]
            except Exception:
                return '***'

        logger = logging.getLogger(__name__)

        payload = None

        # Attempt primary verification using Supabase JWKS / verification key
        try:
            from apps.authentication.jwks import get_verification_key

            verification_key, algorithms = get_verification_key(settings.SUPABASE_URL, token)

            # Debug: log resolved verification metadata without leaking token
            try:
                logger.debug(
                    "JWT verification metadata: algorithms=%s key_type=%s",
                    algorithms,
                    getattr(verification_key, 'key_type', type(verification_key).__name__),
                )
            except Exception:
                logger.debug("JWT verification metadata: unable to introspect verification_key")

            # Use configurable leeway to mitigate clock skew
            leeway = getattr(settings, 'SUPABASE_JWT_LEEWAY', 30)

            payload = jwt.decode(
                token,
                verification_key,
                algorithms=algorithms,
                audience=getattr(settings, 'SUPABASE_JWT_AUD', 'authenticated'),
                options={'verify_aud': True, 'verify_exp': True},
                leeway=leeway,
            )

        except ExpiredSignatureError as e:
            logger.warning("Expired token for incoming request (masked=%s): %s", _mask_token(token), str(e))
            raise exceptions.AuthenticationFailed('Token has expired.')
        except InvalidAudienceError as e:
            logger.error(
                "Invalid audience (expected=%s) for token (masked=%s): %s",
                getattr(settings, 'SUPABASE_JWT_AUD', 'authenticated'),
                _mask_token(token),
                str(e),
            )
            raise exceptions.AuthenticationFailed('Invalid token audience.')
        except InvalidSignatureError as e:
            logger.error("Invalid token signature (masked=%s): %s", _mask_token(token), str(e))
            # Debug: dump JWKS kids to help triage
            try:
                jwks = fetch_jwks(settings.SUPABASE_URL)
                kids = [k.get('kid') for k in jwks.get('keys', [])]
                logger.debug("Available JWKS kids: %s", json.dumps(kids))
            except Exception:
                logger.debug("Unable to fetch/dump JWKS keys for debugging")
            # fall through to HS256 fallback
            payload = None
        except (DecodeError, InvalidAlgorithmError, InvalidTokenError) as e:
            logger.error("Token decode error (%s) for token (masked=%s): %s", e.__class__.__name__, _mask_token(token), str(e))
            payload = None
        except Exception as e:
            logger.exception("Unexpected error during token verification (masked=%s): %s", _mask_token(token), str(e))
            raise exceptions.AuthenticationFailed(f'Token validation error: {str(e)}')

        # If primary verification failed (payload is None), attempt HS256 local fallback
        if not payload:
            try:
                leeway = getattr(settings, 'SUPABASE_JWT_LEEWAY', 30)
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=['HS256'],
                    options={'verify_exp': True},
                    leeway=leeway,
                )
                # Only allow emergency local superuser via this path
                if payload.get('username') != 'EmiMole':
                    logger.error(
                        'HS256 fallback decoded token but username mismatch (masked=%s) payload_username=%s',
                        _mask_token(token),
                        payload.get('username'),
                    )
                    raise exceptions.AuthenticationFailed('Emergency local access strictly limited to EmiMole account.')
                is_local_superuser = True
            except ExpiredSignatureError as e:
                logger.warning('Expired token on HS256 fallback (masked=%s): %s', _mask_token(token), str(e))
                raise exceptions.AuthenticationFailed('Token has expired.')
            except Exception as e:
                logger.exception('HS256 fallback failed for token (masked=%s): %s', _mask_token(token), str(e))
                raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
            
        User = get_user_model()
        
        # If it's a locally signed superuser token
        if is_local_superuser:
            user_id = payload.get('sub')
            try:
                user = User.objects.get(id=user_id, username='EmiMole')
                return (user, token)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed('Local Superuser EmiMole not found.')
                
        # Extract user information from payload
        user_id = payload.get('sub')
        email = payload.get('email')
        role = payload.get('role', 'authenticated')
        app_metadata = payload.get('app_metadata', {})
        user_metadata = payload.get('user_metadata', {})
        
        if not user_id or not email:
            logger.warning("Rejecting token due to missing user_id (%s) or email.", user_id)
            raise exceptions.AuthenticationFailed(
                'Token payload missing required user information.'
            )
            
        # Create or get user from database
        User = get_user_model()
        
        # Muro 2 FIX: Identificar si es un token firmado localmente con el claim 'username' explícito
        local_username = payload.get('username')
        resolve_username = local_username if local_username else user_id

        user, created = User.objects.get_or_create(
            username=resolve_username,
            defaults={
                'email': email,
                'first_name': user_metadata.get('first_name', ''),
                'last_name': user_metadata.get('last_name', ''),
                'is_active': True,
            }
        )
        
        if not created:
            # Update user info if it changed
            if user.email != email:
                user.email = email
                user.save()
        
        # Add Supabase specific attributes to user
        user.supabase_uid = user_id
        user.supabase_role = role
        user.supabase_app_metadata = app_metadata
        user.supabase_user_metadata = user_metadata

        # Map Supabase `role` claim into Django `is_staff` / `is_superuser` flags
        try:
            from apps.authentication.infrastructure.logging_filters import get_anonymized_email, get_hashed_user_id
            
            logger = logging.getLogger(__name__)
            resolved_role = (role or 'authenticated').lower()
            
            # Log minimal auth info with PII sanitizado (el filtro lo hace automáticamente, pero usamos helpers por claridad)
            safe_email = get_anonymized_email(email)
            safe_user_id = get_hashed_user_id(user_id)
            logger.info("auth: sub=%s email=%s role=%s", safe_user_id, safe_email, resolved_role)

            # Promote to staff/superuser ONLY for explicitly privileged roles
            if resolved_role in ('superuser', 'superadmin', 'admin'):
                if not user.is_staff or not user.is_superuser:
                    user.is_staff = True
                    user.is_superuser = True
                    user.save(update_fields=['is_staff', 'is_superuser'])
        except Exception as e:
            # Don't fail authentication due to DB save issues; log and continue
            logging.getLogger(__name__).exception('Error mapping role to user flags: %s', e)

        return (user, token)
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer'


class HardwareAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for Hardware IoT devices.
    
    Validates API Key from `X-Hardware-Api-Key` header.
    This is a machine-to-machine (M2M) authentication method for IoT devices
    (ESP32, Raspberry Pi, etc.) that cannot use JWT tokens.
    
    Usage in views:
        @permission_classes([])  # No permission required, authentication handles it
        @api_view(['POST'])
        def sensor_data_view(request):
            # Use HardwareAPIKeyAuthentication with HardwarePermission
            pass
    """
    
    HEADER_NAME = 'X-Hardware-Api-Key'
    
    def authenticate(self, request):
        """
        Validate the hardware API key from the request header.
        Returns (user, None) if valid, raises AuthenticationFailed if invalid.
        """
        api_key = request.META.get(f'HTTP_{self.HEADER_NAME.upper().replace("-", "_")}')
        
        if not api_key:
            # No API key provided; let other authentication classes handle it
            return None
        
        return self._authenticate_credentials(api_key)
    
    def _authenticate_credentials(self, api_key: str):
        """
        Validate the API key against the configured HARDWARE_API_KEY.
        """
        expected_key = settings.HARDWARE_API_KEY
        
        if not expected_key:
            raise exceptions.AuthenticationFailed(
                'Hardware API authentication is not configured on the server.'
            )
        
        if not hmac.compare_digest(api_key, expected_key):
            raise exceptions.AuthenticationFailed(
                'Invalid hardware API key.'
            )
        
        # Create an anonymous user object for the hardware device
        User = get_user_model()
        # Use a special anonymous user for hardware (no actual user in DB)
        # This allows hardware requests without a real user account
        hardware_user = type('HardwareDevice', (object,), {
            'is_authenticated': False,
            'is_hardware_device': True,
            'username': 'hardware_device',
            'email': 'hardware@iot.local',
            'id': None,
            'is_active': True,
        })()
        
        return (hardware_user, api_key)
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return f'{self.HEADER_NAME}'
