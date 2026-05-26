"""Refresh endpoint for JWT tokens (20‑minute sliding window)."""

from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .infrastructure.local_jwt_auth import LocalJWTAuthentication
import jwt

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([LocalJWTAuthentication])
def refresh_view(request):
    """Return a fresh JWT with a new expiration.
    The client must include the current token in the Authorization header.
    """
    user = request.user
    # Determine role (same as login)
    if user.is_superuser:
        role = "superuser"
    elif user.is_staff:
        role = "admin"
    else:
        role = "user"

    signing_key = getattr(settings, "JWT_SECRET_KEY", None) or settings.SECRET_KEY
    signing_alg = getattr(settings, "JWT_ALGORITHM", "HS256")
    ttl = getattr(settings, "JWT_TTL_MINUTES", 20)

    payload = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": role,
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ttl),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, signing_key, algorithm=signing_alg)
    return Response({"token": token})
