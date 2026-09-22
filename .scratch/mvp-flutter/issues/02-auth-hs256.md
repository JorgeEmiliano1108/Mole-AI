# 02 — Auth unificada HS256 + TokenStore

Status: needs-triage

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Una sola vía app (`LocalJWT HS256`) + una sola vía dispositivos (`HardwareAPIKey + HardwareOnlyPermission`); retirar fallback Supabase hardcodeado (`EmiMole:189`); `TokenStore` 1 key `mole_jwt`; `sessionManager` única autoridad (refresh 15min / inactividad 20min, redirect único `/login.html`); reenviar `Authorization` a MS-3; endpoint `devices/revoke` + rotación con expiración.

## Acceptance criteria

- [ ] `pytest` auth: login/refresh/exp/401/rotación/revocación en verde
- [ ] E2E `test_jwt_auth.sh` en verde con `JWT_SECRET` de test
- [ ] `pytest` flujo API login→metadata→refresh(jti rota)→logout→401 + ARCO
      (`apps/authentication/tests/test_auth_flow_e2e.py`; reemplaza spec Playwright, pivot V2)
- [ ] `DELETE profile` anonimiza PII + `AuditLog` append-only (LFPDPPP)
- [ ] Sin `os.path.join` con input usuario en auth/uploads

## Blocked by

- `01-gobernanza-harness.md`

## Comments

- 2026-09-07 (agente): verificado `login_view:254-264` emite HS256 `aud=authenticated + username + exp TTL 20min`, coherente con `LocalJWTAuthentication:58-65`. Sin asumir JWKS: `jwks.py:17` retorna clave local, no JWKS real (ADR-0003 lo difiere).
- 2026-09-07 (agente): fix aplicado en `infrastructure/authentication.py:186-192` — eliminado hardcode `username='EmiMole'`; ahora `get(id=sub, is_superuser=True)`. `py_compile` OK. Compatibilidad: `setup_superuser.py` siembra un superuser llamado EmiMole (seed legítimo) y `test_mlops_upload.py` minta JWT para él — ambos siguen funcionando al ser superuser real. Resto `EmiMole` solo en seeds/tests, sin lógica auth.
- Pendiente (requiere CI con node/pytest vivo): `TokenStore` 1 key `mole_jwt` en `frontend/.../config.js + ApiService.js`, redirect único `/login.html`, forward `Authorization` a MS-3, `devices/revoke` + rotación con expiración (cambio modelo `Device` + migración).
- Skills: `diagnose` (hipótesis backdoor verificada en código), `tdd` (tests existentes `test_login_dual` como red previa al refactor JS), `enforce-compliance` LFPDPPP (sin PII en logs del fix).
