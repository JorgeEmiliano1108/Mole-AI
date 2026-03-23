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
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """
    GET    /api/v1/auth/profile/ — Return the authenticated user's profile.
    PATCH  /api/v1/auth/profile/ — Update mutable profile fields.
    DELETE /api/v1/auth/profile/ — Derecho ARCO: eliminación de cuenta.
           Anonimiza PII y elimina el usuario. Los registros científicos
           (SensorLog, AIDiagnostic) se conservan con user_id/plant_id = NULL
           gracias a on_delete=SET_NULL en las FK relacionadas.
    """
    user = request.user

    if request.method == "GET":
        return Response({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar_url": getattr(user, "avatar_url", None),
            "phone_number": getattr(user, "phone_number", None),
            "supabase_uid": getattr(user, "supabase_uid", None),
            "supabase_role": getattr(user, "supabase_role", "authenticated"),
            "is_premium": getattr(user, "is_premium", False),
            "data_consent": getattr(user, "data_consent", False),
            "data_consent_date": getattr(user, "data_consent_date", None),
        })

    if request.method == "DELETE":
        user_id = user.id
        ip_addr = request.META.get("REMOTE_ADDR")
        # Wipe PII before deletion for LFPDPPP compliance (Derecho de Cancelación)
        user.first_name = ""
        user.last_name = ""
        user.email = f"deleted_{user_id}@anonimizado.mole.ai"
        user.phone_number = None
        user.avatar_url = None
        user.supabase_uid = None
        user.supabase_user_metadata = {}
        user.is_active = False
        user.save()
        # Delete triggers SET_NULL on UserPlant, DiagnosticoGeolocalizado,
        # FeedbackTicket — preserving scientific data integrity.
        user.delete()
        
        # MoProSoft: Trazabilidad inmutable
        from apps.core.infrastructure.repositories.models import AuditLog
        AuditLog.objects.create(
            user_id=user_id,
            action="DELETE_ACCOUNT_ARCO",
            ip_address=ip_addr,
            details=f"Account {user_id} deleted and PII wiped."
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH — only allow safe mutable fields
    allowed = {"first_name", "last_name", "avatar_url", "phone_number"}
    updated = []
    for field, value in request.data.items():
        if field in allowed:
            setattr(user, field, value)
            updated.append(field)

    if not updated:
        return Response(
            {"error": "No se enviaron campos válidos para actualizar.",
             "allowed_fields": sorted(allowed)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user.save(update_fields=updated + ["updated_at"])
    return Response({"status": "updated", "fields": updated})


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def user_subscription_view(request):
    """
    GET /api/v1/auth/subscription/ — Current subscription status.
    PUT /api/v1/auth/subscription/ — (placeholder for Stripe/webhook integration).
    """
    user = request.user
    if request.method == "GET":
        return Response({
            "is_premium": getattr(user, "is_premium", False),
            "subscription_expires": getattr(user, "subscription_expires", None),
            "has_active_subscription": (
                user.has_subscription()
                if hasattr(user, "has_subscription") else False
            ),
        })
    # PUT — reserved for payment webhook integration
    return Response(
        {"message": "Subscription updates will be handled via payment webhook."},
        status=status.HTTP_501_NOT_IMPLEMENTED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_metadata_view(request):
    """
    GET /api/v1/auth/metadata/ — Supabase JWT claims attached during authentication.
    """
    user = request.user
    return Response({
        "supabase_uid": getattr(user, "supabase_uid", None),
        "supabase_role": getattr(user, "supabase_role", None),
        "app_metadata": getattr(user, "supabase_app_metadata", {}),
        "user_metadata": getattr(user, "supabase_user_metadata", {}),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    POST /api/v1/auth/logout/ — Stateless API Logout
    En REST JWT, la invalidación del token debe hacerse borrando el token 
    en el cliente (Frontend). No mantenemos sesiones de lado del servidor.
    """
    return Response({
        "status": "logged_out", 
        "message": "Token must be discarded by client."
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    """
    POST /api/v1/auth/register/
    Registra a un nuevo agricultor u operador de manera local con la contraseña hasheada.
    """
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email")

    if not username or not password:
        return Response({"error": "Faltan credenciales."}, status=status.HTTP_400_BAD_REQUEST)

    if "@" in username and not email:
        email = username
        username = username.split("@")[0] + "_user"

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if User.objects.filter(username=username).exists():
        return Response({"error": "El usuario ya existe."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    user.is_active = True
    user.save()

    return Response({
        "status": "created",
        "username": user.username
    }, status=status.HTTP_201_CREATED)

@api_view(["POST"])
@permission_classes([AllowAny])
def validate_token_view(request):
    """
    POST /api/v1/auth/validate-token/
    Accepts a Supabase JWT in the Authorization header, validates it,
    creates/updates the Django user, and returns user info.
    Used as the "login" handshake for the mobile/web client.
    """
    username = request.data.get("username")
    password = request.data.get("password")

    # Hybrid Auth Protocol: Local authentication bypass
    if username and password:
        from django.contrib.auth import authenticate, get_user_model
        from django.conf import settings
        import jwt
        from datetime import datetime, timedelta, timezone
        
        User = get_user_model()
        if "@" in username:
            user_obj = User.objects.filter(email=username).first()
            if user_obj:
                username = user_obj.username

        user = authenticate(request=request, username=username, password=password)
        if user is not None:
            # Generar JWT local compatible con SupabaseAuthentication
            role = "superuser" if user.is_superuser else "user"
            # Preferimos usar SUPABASE_JWT_SECRET/ALGORITHM si están disponibles
            signing_key = getattr(settings, 'SUPABASE_JWT_SECRET', None) or settings.SECRET_KEY
            signing_alg = getattr(settings, 'SUPABASE_JWT_ALGORITHM', 'HS256')

            payload = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": role,
                "aud": "authenticated",
                "exp": datetime.now(timezone.utc) + timedelta(days=1),
                "iat": datetime.now(timezone.utc),
            }

            token = jwt.encode(payload, signing_key, algorithm=signing_alg)
            return Response({
                "token": token,
                "role": role
            })
        else:
            return Response(
                {"error": "Credenciales inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    # Supabase authentication fallback
    from apps.authentication.infrastructure.authentication import SupabaseAuthentication

    auth = SupabaseAuthentication()
    try:
        result = auth.authenticate(request)
    except Exception as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if result is None:
        return Response(
            {"error": "Authorization header con Bearer token requerido."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    user, token = result
    return Response({
        "status": "authenticated",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "supabase_uid": getattr(user, "supabase_uid", None),
            "is_premium": getattr(user, "is_premium", False),
        },
    })


class AuthHealthCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "Authentication Module",
            "version": "2.0.0",
        })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_debug_view(request):
    return Response({
        "user": str(request.user),
        "auth_header": request.META.get("HTTP_AUTHORIZATION", "None"),
        "is_authenticated": request.user.is_authenticated,
        "supabase_uid": getattr(request.user, "supabase_uid", None),
    })