# ADR-0003: HS256 local como auth del MVP (JWKS diferido a fase 2)

- **Fecha:** 2026-09-07
- **Estado:** Aceptado
- **Contexto:** Cuatro sistemas conviven: `DualLoginBackend` (sesión web), `LocalJWT HS256` (`local_jwt_auth.py`), `SupabaseAuthentication` (fallback con `hardcode EmiMole:189`, `jwks.py` ya no es JWKS real), `HardwareAPIKey` (usuario fantasma `is_authenticated=False`). El APK debe funcionar en campo sin internet (sin JWKS remoto) y el E2E usa `JWT_SECRET=test-secret-key-for-e2e-tests` HS256. Alternativa: exigir JWKS/Supabase ya.
- **Decisión:** MVP = `LocalJWT HS256` (app) + `HardwareAPIKey + HardwareOnlyPermission` (dispositivos). Retirar fallback Supabase hardcodeado; `DualLogin` solo sesión web tras flag. JWKS real + rotación `auth_token` con expiración → fase 2.
- **Consecuencias:** Menos dependencias externas, `flutter_secure_storage` + `refresh 15min / inactividad 20min` ya probados. Riesgo: lockout `Axes 5` y claves sin rotación → mitigado con endpoint `devices/revoke` + rotación en Slice 1 + `diagnose` loop.
- **Cumplimiento:** `enforce-compliance` Guardrail A (LFPDPPP: ciclo de vida del dato, `DELETE profile` anonimiza + `AuditLog` append-only) + ISO 25001 seguridad.
