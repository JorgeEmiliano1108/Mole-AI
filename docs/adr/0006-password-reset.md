# ADR-0006: Recuperación de contraseña con tokens de un solo uso

- **Fecha:** 2026-09-21
- **Estado:** Aceptado
- **Contexto:** No existe flujo olvidé-contraseña (`grep password.reset` vacío; solo `verify-email`/`resend-verification`). Un usuario móvil que olvida su contraseña queda bloqueado.
- **Decisión:** `POST auth/password-reset/request {email}` → siempre 202 (anti-enumeración) + mail con token un solo uso TTL 1h; `POST auth/password-reset/confirm {token,new_password}` (reutiliza `validate_password_strength`); `POST auth/password-change` autenticado; throttle/Axes como login; `AuditLog` en cada paso; tokens hash SHA-256 en DB (nunca plaintext, patrón `email_verification_token` en `tasks.py:23-65`).
- **Consecuencias:** Sin dependencias nuevas; el APK añade pantallas request/confirm; la web no existe (retirada).
- **Cumplimiento:** `enforce-compliance` LFPDPPP + Guardrail B (firma completa, rate-limit).
