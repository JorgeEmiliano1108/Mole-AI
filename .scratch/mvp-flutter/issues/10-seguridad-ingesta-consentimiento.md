# 10 — Seguridad ingesta + consentimiento (S09 parcial)

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Cerrar `AllowAny` en `edge-batch` sin romper firmware; throttles faltantes;
rotación `auth_token` con expiración; consentimiento LFPDPPP en backend;
página `/privacy`; test resiliencia MQTT; higiene deuda en docs + CONTEXT.

## Acceptance criteria

- [x] `DeviceBearerPermission` + `DeviceBearerScheme` (401, Bearer por dispositivo)
- [x] Throttles en `sensor_batch_view`, `diagnostic_view`, `llm_chat_view`, edge-batch
- [x] Migraciones `0012` (expiración) + `0013` (FK owner → `AUTH_USER_MODEL`)
- [x] `POST devices/<id>/rotate/` (owner/staff) + `POST auth/consent/` + `AuditLog`
- [x] `frontend/privacy.html` + link + POST best-effort desde banner
- [x] Django unit 24/24 (rotación 7, consent 4, mqtt-resiliencia 1, env 9, middleware/health/metrics 3)
- [x] E2E sistema jwt + nom059 + chat en verde
- [x] Suite amplia: 40 passed, resto pre-existente idéntico a baseline (archivo por archivo)
- [x] CONTEXT.md con deuda canónica; stales corregidos (wait-for-services, S3, OTEL, FSM 12+1)

## Blocked by

None - can start immediately

## Comments

- 2026-09-14 (agente): skills `enforce-compliance`, `tdd`, `diagnose`, `grill-with-docs`, `improve-codebase-architecture`.
- Hallazgo mayor: FK `devices.owner_id` → tabla inexistente `auth_user` (migración 0010 con `to='auth.User'`); en DB fresca rompía TODA escritura de dispositivos. Corregido con 0013.
- Cadena de 401s diagnosticada por capas: `LocalJWT` vs token opaco → `authentication_classes=[DeviceBearerScheme]`; middleware capturaba `edge-batch` por prefijo → bypass si no parece JWT (2 puntos); DRF degrada a 403 sin header → scheme lo declara.
- Throttle exige Redis (compose OK; tests usan locmem). Sin Redis local, `GracefulDegradationMiddleware` responde 503 (verificado).
- Abierto (requiere usuario): rotar password RDS y borrar `.env.bak`; cerrar 1883/`allow_anonymous` (fase 2, toca firmware); `TokenStore` 1-key JS; `test_login_dual` y `test_nom059` en verde (ambientales py3.14/sqlite).
- 2026-09-15 (agente): plan deuda docs+código (skills `diagnose`, `tdd`, `grill-with-docs`, `triage`, `enforce-compliance`). `/tmp` se limpió entre sesiones → venv reconstruido (`python3 -m venv`, `requirements.txt`, +`ruff` para criterio AGENTS.md).
- Step 0: `test_audit.py` roto por edición previa (`IndentationError` tras `try:` + refs a `eager`/`override_settings` eliminados). Reescrito: `.apply(throw=True)` eleva `Retry` (verificado en `celery/app/task.py`: `throw=False` traga en `EagerResult`; `run()` directo re-eleva original por `called_directly`); backend `memory://` con restore en `finally`; parche a `celery.app.trace.logger` (call-sites `info:128` y `_log_error:309` rompen con stdlib en Celery 5.6.3). Suite 19 ficheros: **61 passed**.
- Step 1: `scripts/clean_secrets.py` alineado al env genérico (24 sensibles incl. `DB_PASSWORD`/`LLM_API_KEY`/`OBJECT_STORAGE_*`; fuera `HUGGINGFACE_*`/`HF_*`/`SUPABASE_*`); `ruff check` limpio en los 4 archivos tocados (`TRY401`+`BLE001`+imports+`SIM117` corregidos; `chmod +x` por `EXE001`).
- Step 2: `docs/system-reminder.md` §8 actualizado — `tflite_adapter.py` eliminado de la tabla (archivo inexistente; TD-02 resuelto), MinIO mitigado (solo notas de remoción `docker-compose.yml:336-337`), CI existe/falta CD, resiliencia parcial (faltan Redis-down/PG-down).
- Sigue abierto (requiere usuario): rotación RDS + borrar `.env.bak`; cierre 1883 (fase 2 firmware); roles granulares; fallback ONNX; retención `botanical_knowledge`; Alertmanager/Grafana.
- 2026-09-18 (agente, B7 runbook rotación — decisión usuario: solo rotación, sin purge).
  Estado verificado: 0 secretos trackeados (`git ls-files` limpio de `.env*`,
  `key.properties`, `*.jks/pem/key`); `.env.bak` y `.env.production.template`
  eliminados del disco; `.gitignore` cubre `.env*` y `key.properties`.
  Historial con secretos (nombres de archivo, sin valores): `.env` en `2df786e`
  (`ADMIN_API_KEY`, `FARMER_API_KEY`) y `f568e4b` (remoción); `mole_report/.env`
  en `3fea875`; `esp32_node/build/config.env` en `4e367be`/`3fea875`.
  Checklist usuario (en ventana de bajo tráfico):
  1. RDS: reset password en consola AWS → actualizar `DB_PASSWORD`/`DB_URL` en
     `.env` (y secrets manager) → `GET /api/v1/health/` + login OK.
  2. NVIDIA (`LLM_API_KEY`), IdP (`IDP_*`), S3 (`OBJECT_STORAGE_*`): rotar si los
     valores del historial siguen vivos en algún entorno.
  3. Verificar: `git ls-files | grep -E '\.env|key|pem'` vacío (salvo `ca.crt`
     pública) + `python scripts/clean_secrets.py` sin hallazgos nuevos.
  4. Ventana 20min: los JWT viejos expiran solos; para corte inmediato usar
     `POST devices/<id>/revoke/` (flota) — usuarios: basta rotación + expiración.
