"""Revocación de sesión B3: jti + denylist.

- login/refresh emiten `jti`.
- logout publica el `jti` → el token viejo responde 401.
- refresh rota `jti` (el anterior sigue válido hasta su `exp`: sliding window).
- tokens legacy sin `jti` siguen válidos hasta expirar.
Caché locmem para hermeticidad (prod usa Redis).
"""
import jwt as pyjwt
import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

User = get_user_model()

LOC = {
    "CACHES": {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
}


def _login(client, username="sess1", password="Segura123!"):
    User.objects.create_user(username=username, password=password)
    resp = client.post(
        "/api/v1/auth/login/",
        {"username": username, "password": password},
        format="json",
    )
    assert resp.status_code == 200, resp.content[:200]
    return resp.json()["token"]


def _claims(token):
    from django.conf import settings
    key = getattr(settings, "JWT_SECRET_KEY", None) or settings.SECRET_KEY
    return pyjwt.decode(
        token, key, algorithms=["HS256"], audience="authenticated",
        options={"verify_exp": False},
    )


@pytest.mark.django_db
@override_settings(**LOC)
def test_login_emite_jti():
    token = _login(APIClient())
    assert _claims(token).get("jti"), "login debe emitir jti"


@pytest.mark.django_db
@override_settings(**LOC)
def test_logout_revoca_token_viejo():
    client = APIClient()
    token = _login(client)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert client.get("/api/v1/auth/metadata/").status_code == 200
    assert client.post("/api/v1/auth/logout/").status_code == 200
    # Token revocado → 401 aunque no haya expirado.
    resp = client.get("/api/v1/auth/metadata/")
    assert resp.status_code == 401, resp.content[:200]


@pytest.mark.django_db
@override_settings(**LOC)
def test_refresh_rota_jti():
    client = APIClient()
    token = _login(client)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    resp = client.post("/api/v1/auth/refresh/")
    assert resp.status_code == 200
    new_token = resp.json()["token"]
    assert _claims(new_token)["jti"] != _claims(token)["jti"]


@pytest.mark.django_db
@override_settings(**LOC)
def test_legacy_sin_jti_sigue_valido():
    from datetime import datetime, timedelta, timezone

    from django.conf import settings
    user = User.objects.create_user(username="legacy1", password="x")
    key = getattr(settings, "JWT_SECRET_KEY", None) or settings.SECRET_KEY
    now = datetime.now(timezone.utc)
    token = pyjwt.encode(
        {"sub": str(user.id), "username": user.username,
         "email": user.email, "role": "user", "aud": "authenticated",
         "exp": now + timedelta(minutes=20), "iat": now},
        key, algorithm="HS256",
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert client.get("/api/v1/auth/metadata/").status_code == 200
