# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Celery tasks for authentication operations.
"""
import hashlib
import secrets
import os
from celery import shared_task
from django.utils import timezone
from django.conf import settings


def generate_email_token(user_id: int) -> str:
    """Genera token de verificación único (32 bytes hex)."""
    random_bytes = secrets.token_bytes(32)
    return hashlib.sha256(
        f"{random_bytes.hex()}{user_id}{settings.SECRET_KEY}".encode()
    ).hexdigest()[:64]


@shared_task(name="send_verification_email_task")
def send_verification_email_task(user_id: int, email: str, username: str):
    """
    Envía correo de verificación al nuevo usuario.
    Generates token, saves to DB, and sends verification link.
    """
    from django.core.mail import send_mail
    from apps.authentication.models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return "User not found"

    token = generate_email_token(user_id)
    user.email_verification_token = token
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=["email_verification_token", "email_verification_sent_at"])

    base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:8080")
    verify_url = f"{base_url}/verify-email/{token}"

    subject = "Mole.AI — Verifica tu correo electrónico"
    message = (
        f"Hola {username},\n\n"
        f"Gracias por registrarte en Mole.AI.\n\n"
        f"Para verificar tu correo electrónico, haz clic en el siguiente enlace:\n"
        f"{verify_url}\n\n"
        f"Si no solicitaste este registro, puedes ignorar este correo.\n\n"
        f"— El equipo de Mole.AI"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return f"Verification email sent to {email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"


@shared_task(name="verify_email_task")
def verify_email_task(token: str):
    """
    Verifica el correo electrónico usando el token.
    """
    from apps.authentication.models import User

    try:
        user = User.objects.get(email_verification_token=token)
        user.is_email_verified = True
        user.email_verification_token = None
        user.save(update_fields=["is_email_verified", "email_verification_token"])
        return {"status": "verified", "user_id": user.id}
    except User.DoesNotExist:
        return {"status": "invalid_token"}