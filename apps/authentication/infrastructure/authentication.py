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
            # Decode the JWT token using Supabase secret
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=[settings.SUPABASE_JWT_ALGORITHM],
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