"""Denylist de JWT por `jti` (B3, revocación de sesión).

Diseño:
- Cada JWT emitido (`login_view`, `refresh_view`) porta `jti = uuid4().hex`.
- `logout_view` publica el `jti` en caché con TTL = vida restante del token.
- `LocalJWTAuthentication` rechaza tokens cuyo `jti` esté publicado.
- Tokens legacy sin `jti` siguen válidos (compatibilidad; su riesgo se acota
  a `JWT_TTL_MINUTES` por expiración natural).
- Backend de caché: `django.core.cache` (locmem en tests, Redis en prod).
  Si la caché falla se permite el paso con warning (fail-open documentado:
  la revocación es best-effort y la expiración ≤20min acota la ventana;
  sin Redis el middleware de degradación ya responde 503).
"""
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

_PREFIX = "jwt_denylist:"


def deny_jti(jti, ttl_seconds):
    """Publica un `jti` como revocado durante `ttl_seconds`."""
    if not jti:
        return
    try:
        cache.set(f"{_PREFIX}{jti}", True, timeout=max(1, int(ttl_seconds)))
    # Cualquier backend de caché puede fallar; revocación best-effort.
    except Exception as exc:  # noqa: BLE001
        logger.warning("Denylist no disponible al revocar jti: %s", exc)


def is_denied(jti):
    """True si el `jti` está revocado. Sin `jti` (legacy) → False."""
    if not jti:
        return False
    try:
        return bool(cache.get(f"{_PREFIX}{jti}"))
    # Fail-open documentado: la expiración ≤20min acota la ventana.
    except Exception as exc:  # noqa: BLE001
        logger.warning("Denylist no disponible al validar jti: %s", exc)
        return False
