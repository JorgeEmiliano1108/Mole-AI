from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """
    GET  /api/v1/auth/profile/ — Return the authenticated user's profile.
    PATCH /api/v1/auth/profile/ — Update mutable profile fields.
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
        })

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
    POST /api/v1/auth/logout/ — Server-side session invalidation.
    JWT invalidation is handled by Supabase; this clears the Django session.
    """
    if hasattr(request, "session"):
        request.session.flush()
    return Response({"status": "logged_out"})


@api_view(["POST"])
@permission_classes([AllowAny])
def validate_token_view(request):
    """
    POST /api/v1/auth/validate-token/
    Accepts a Supabase JWT in the Authorization header, validates it,
    creates/updates the Django user, and returns user info.
    Used as the "login" handshake for the mobile/web client.
    """
    from authentication.infrastructure.authentication import SupabaseAuthentication

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