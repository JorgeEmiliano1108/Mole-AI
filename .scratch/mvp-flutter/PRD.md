# PRD — MVP migrable a Flutter (APK)

## Problem Statement

El frontend web (MPA Vite) acumula deuda no portable a móvil (`document/window`, `localStorage` x15 keys, Leaflet, Chart.js/echarts, jsPDF/Blob, WebBLE, `192.168.4.1`) y el backend expone contratos duplicados (auth x4, ingesta x4, chat sync/async, doble PDF, `batch` vs `edge-batch`). Sin congelar contratos + fachadas repository, el APK Flutter hereda la deuda.

## Solution

Slices verticales que consolidan backend → congelan contrato OpenAPI → aíslan fachadas → cubren con pytest/vitest/E2E. Resultado: `mobile/` greenfield (`Dio+Riverpod+flutter_map`) contra API estable.

## User Stories

- Como usuario, quiero login/refresh/logout en el APK con sesión segura, para usar la app en campo.
- Como usuario, quiero buscar especies y ver disclaimer NOM-059, para no extraer flora protegida.
- Como usuario, quiero ver telemetría y salud de mis especímenes, incluso con nodos dormidos (deep-sleep 5min).
- Como usuario, quiero diagnosticar por foto y recibir especie/severidad/pH/confianza.
- Como usuario, quiero chatear con contexto de mi planta + sensores.
- Como usuario, quiero ver mapa de hotspots + clima.
- Como usuario, quiero descargar el reporte PDF del diagnóstico.

## Implementation Decisions

- Auth MVP HS256 local (ADR-0003); JWKS fase 2.
- Ingesta canónica trama edge (ADR-0002); móvil solo lectura.
- Un serializer/validación por dominio (magic-bytes + `safe_join` en uploads).
- Fachadas `*Repository` puras antes de Dart; nada `document/window/navigator` cruza a móvil.

## Testing Decisions

- Pirámide: unit `pytest -m unit` (<2s) + `flutter_test`; integración `APITestCase`; E2E `docker-compose.e2e` + `integration_test` Flutter contra backend real (pivot V2 2026-09-21: web retirada; cero Playwright/vitest/msw en el repo).
- Buenos tests: vía API pública, sobreviven refactor, `Disclaimers/NOM-059` y `path-traversal` siempre cubiertos.
- Gates: `ruff+pyright+pytest --cov-fail-under=80`, `flutter analyze + flutter test`, SonarQube 0 Blocker.

## Out of Scope

Riego auto/PID/hídrico, geocercas, XLSX, ECharts avanzado, BLE provisioning completo + mapa offline (fase 2), `ai_rag_service` stub.

## Further Notes

Tracker: `.scratch/mvp-flutter/issues/` con `Status:`; migrar a GitHub Issues al congelar MVP. Compliance: `enforce-compliance` en cada slice.

## Progreso 2026-09-17 (Fases 0–3 ejecutadas, secuencial)

- Fase 0: contrato congelado — `docs/mobile-contract.md` + snapshot `docs/contracts/openapi.yml`
  (77 paths) + gate CI `mobile-contract` (job en `system-tests.yml`, script
  `scripts/check-mobile-contract.sh`, verificado GREEN+RED). Issues 11+12 creados.
  Vías congeladas: visión async Django+Celery, chat gateway (fase 2).
- Fase 1: `DEFAULT_PAGINATION_CLASS` 50 + `GET health/` público + orden `favorites/`;
  `tests/test_mobile_contract_fase1.py` (3 tests); snapshot regenerado por protocolo.
- Fase 2–3: `mobile/` (Flutter 3.44, Dio+Riverpod+secure_storage+image_picker):
  `flutter analyze` 0 issues, `flutter test` 24 passed,
  `app-release.apk` 51MB (debug-keys, interno). MVP recortado completo en APK.
- Pendiente: fase 2 (chat/mapa/reportes), keystore prod, tests Redis-down/PG-down,
  roles granulares, rotación RDS/`.env.bak` (usuario).

## Progreso 2026-09-17 bis — 100% teléfono (Fases A–G, 7 historias + offline + release)

- Fase A: permisos mínimos (`INTERNET/CAMERA/ACCESS_NETWORK_STATE`, sin LOCATION/STORAGE),
  label `Mole.AI`, keystore release RSA-2048/30a (`/home/paul/.mole-android/`,
  SHA-256 `fd3f2b0b…a7574e`) + `signingConfigs.release` con fallback debug (CI).
  Lección: PKCS12 ignora keypass ≠ storepass → ambos iguales.
- Fase B: 9 hallazgos de coherencia corregidos en `mobile-contract.md`.
- Fase C: 7 defectos UX (logout único, `e.message`+retry, validación, contraste NOM-059
  sólido, scroll/SafeArea, autofill+Semantics, vacíos).
- Fase D: chat gateway + mapa flutter_map + reportes MS3 (prefijo `/api/v1/reports`
  reparado en `mole_report/app/main.py` — Django admin y nginx ya lo llamaban así).
- Fase E: offline real (caché TTL + cola de fotos con auto-subida; chat/análisis/reportes
  exigen red por arquitectura).
- Fase F: backend verificado sobre HTTP real; `app-release.apk` 53.9MB firmada
  (`apksigner verify` OK). Staging duckdns inalcanzable → probar por LAN o desplegar.
- Métricas: `flutter analyze` 0 issues, `flutter test` 39 passed, Django 64 passed,
  gate contrato verde.
- Pendiente usuario: respaldar keystore, rebuild con URL real, rotación RDS/`.env.bak`,
  invalidar legacy keys del historial, deploy staging, MS-16, Redis/PG-down.
