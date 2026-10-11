# ADR-0006: Recuperación de contraseña con tokens de un solo uso

- **Fecha:** 2026-09-21
- **Estado:** Aceptado
- **Contexto:** No existe flujo olvidé-contraseña (`grep password.reset` vacío; solo `verify-email`/`resend-verification`). Un usuario móvil que olvida su contraseña queda bloqueado.
- **Decisión:** `POST auth/password-reset/request {email}` → siempre 202 (anti-enumeración) + mail con token un solo uso TTL 1h; `POST auth/password-reset/confirm {token,new_password}` (reutiliza `validate_password_strength`); `POST auth/password-change` autenticado; throttle/Axes como login; `AuditLog` en cada paso; tokens hash SHA-256 en DB (nunca plaintext, patrón `email_verification_token` en `tasks.py:23-65`).
- **Consecuencias:** Sin dependencias nuevas; el APK añade pantallas request/confirm; la web no existe (retirada).
- **Cumplimiento:** `enforce-compliance` LFPDPPP + Guardrail B (firma completa, rate-limit).

## Enmienda 2026-10-06 — Degradación honesta sin SMTP (Wave D, decisión de usuario)

- **Contexto:** no existe proveedor SMTP configurado (`settings.py` no define `EMAIL_BACKEND/HOST`; `.env.example` tampoco). El `202` incondicional mentía: el correo jamás salía y la anti-enumeración ocultaba un no-envío.
- **Decisión:** `POST auth/password-reset/request` responde **501** (`PASSWORD_RESET_EMAIL_ENABLED=false`, default) con mensaje genérico cuando el correo no está habilitado. Con SMTP real + flag `true`, el flujo original (202 anti-enumeración + token un solo uso TTL 1h) opera intacto.
- **Consecuencias:** el APK debe mapear 501 a "recuperación no disponible, contacta soporte" (contrato móvil §1); sin credenciales ni costos nuevos. Issue de seguimiento para el alta de proveedor.
- **Cumplimiento:** silent-compliance (sin detalle interno en la respuesta); `AuditLog` solo se emite cuando el flujo real se ejecuta.
