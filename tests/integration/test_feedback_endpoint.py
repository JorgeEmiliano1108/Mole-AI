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
Integration tests for POST /api/v1/feedback/  (FeedbackTicket creation).
Verifies:
  - Authenticated user can create a ticket (201 Created).
  - Unauthenticated request is rejected (401 Unauthorized).
  - Invalid payload is rejected (400 Bad Request).
"""
import pytest
from typing import Any, cast
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_feedback_create_returns_201_for_authenticated_user():
    """POST /api/v1/feedback/ with valid payload → 201 + ticket data."""
    user = User.objects.create_user(
        username="farmer_test",
        password="secureP@ss123",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "topic": "bug",
        "message": "El diagnóstico muestra 'healthy' pero la planta tiene manchas.",
    }

    with patch("core.presentation.views.FeedbackTicket.objects.create") as create_mock:
        fake_ticket = MagicMock()
        fake_ticket.id = 42
        fake_ticket.user = user
        fake_ticket.topic = "bug"
        fake_ticket.message = payload["message"]
        fake_ticket.status = "open"
        fake_ticket.created_at = "2026-03-15T12:00:00Z"
        create_mock.return_value = fake_ticket

        response = cast(Any, client.post(
            "/api/v1/feedback/",
            data=payload,
            format="json",
        ))

    assert response.status_code == 201
    assert response.data["id"] == 42
    assert response.data["topic"] == "bug"
    assert response.data["status"] == "open"
    create_mock.assert_called_once_with(
        user=user,
        topic="bug",
        message=payload["message"],
    )


@pytest.mark.django_db
def test_feedback_create_returns_401_without_authentication():
    """POST /api/v1/feedback/ without auth → 401."""
    client = APIClient()

    payload = {
        "topic": "suggestion",
        "message": "Sería útil poder ver historial de pH por semana.",
    }

    response = cast(Any, client.post(
        "/api/v1/feedback/",
        data=payload,
        format="json",
    ))

    assert response.status_code == 401


@pytest.mark.django_db
def test_feedback_create_returns_400_for_invalid_payload():
    """POST /api/v1/feedback/ with missing/short fields → 400."""
    user = User.objects.create_user(
        username="farmer_bad",
        password="secureP@ss123",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    # message too short (min_length=10)
    payload = {"topic": "bug", "message": "short"}

    response = cast(Any, client.post(
        "/api/v1/feedback/",
        data=payload,
        format="json",
    ))

    assert response.status_code == 400
    assert "details" in response.data
