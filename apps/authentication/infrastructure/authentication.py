import hmac

from rest_framework import authentication, exceptions
from django.conf import settings
import jwt
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
        try:
            # Auto-detect algorithm and get correct verification key
            from apps.authentication.jwks import get_verification_key
            verification_key, algorithms = get_verification_key(
                settings.SUPABASE_URL, token
            )
            
            # Decode the JWT token using the resolved key
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
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired.')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Token validation error: {str(e)}')
            
        # Extract user information from payload
        user_id = payload.get('sub')
        email = payload.get('email')
        role = payload.get('role', 'authenticated')
        app_metadata = payload.get('app_metadata', {})
        user_metadata = payload.get('user_metadata', {})
        
        if not user_id or not email:
            raise exceptions.AuthenticationFailed(
                'Token payload missing required user information.'
            )
            
        # Create or get user from database
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=user_id,
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
