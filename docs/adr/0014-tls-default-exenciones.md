# ADR-0014: `SECURE_SSL_REDIRECT` default `True` en prod + exenciones

- **Fecha:** 2026-10-06
- **Estado:** Aceptado (Wave D; cierra brecha RNF-BE-02 del PRD de trazabilidad)
- **Contexto:** `SECURE_SSL_REDIRECT` dependía del proxy para forzar HTTPS; su default efectivo dejaba HTTP plano posible a nivel app. `.env.example` además fijaba `SECURE_SSL_REDIRECT=False` con `DEBUG=False`, contradicción documentada.
- **Decisión:**
  1. `SECURE_SSL_REDIRECT` default `True` cuando `DEBUG=false` (`core_backend/mole_ai_backend/settings.py:72-74`); en desarrollo local (`DEBUG=true`) sigue `False` para no romper el setup HTTP.
  2. Exenciones mínimas y auditables: `SECURE_REDIRECT_EXEMPT = [^health/$, ^api/schema/$]` (`settings.py:77`) — probes de balanceadores y schema público pre-login no deben redirigir.
  3. `.env.example` corregido a `SECURE_SSL_REDIRECT=True` (coherente con `DEBUG=False`).
- **Consecuencias:** el proxy (Nginx/ALB) solo termina TLS, ya no lo sustituye; RNF-BE-02 → ✅. Operadores que necesiten HTTP interno deben declararlo explícito por env, nunca por default.
- **Cumplimiento:** `enforce-compliance` guardrail telemetría-solo-con-TLS; IFT-016.
