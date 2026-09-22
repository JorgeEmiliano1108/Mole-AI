# 08 — Hardening, CI y scaffold mobile/

Status: needs-triage

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Split `settings/base|dev|prod`, `PageNumberPagination 50`, `docs/docker-hardening.md` (o retirar refs RNF-34/35), corrección README claims (`~900→83` tests, apps reales, CORS en nginx, DRF throttles), `pre-commit ruff+pytest`, `check-docs-consistency` en CI, `plugin.json` (añadir 4 misc o documentar omisión), y `flutter create mobile` + `Dio+Riverpod+flutter_map` + `flutter build apk --release` firmada.

## Acceptance criteria

- [ ] `ruff + pyright + pytest --cov-fail-under=80` en verde en CI
- [ ] `flutter analyze + flutter test` en verde en CI (pivot V2, sin vitest)
- [ ] SonarQube 0 Blocker en archivos tocados
- [x] `flutter build apk --release` genera APK instalable contra `https://api…/api/v1/` (sin `http` claro salvo setup)
  - 2026-09-17: `mobile/build/app/outputs/flutter-apk/app-release.apk` (53.9MB) construido en
    `ghcr.io/cirruslabs/flutter:stable` (Flutter 3.44/Dart 3.12) con
    `--dart-define=API_BASE_URL=https://…/api/v1/`. **Firmado release**
    (`apksigner verify` OK, SHA-256 `fd3f2b0b…a7574e`, RSA 2048/30a en
    `/home/paul/.mole-android/`, `key.properties` gitignored).
    Lección: PKCS12 ignora keypass distinto al storepass (keytool lo avisa y
    AGP falla con BadPadding) → ambos iguales. `flutter analyze`: 0 issues.
    `flutter test`: 39 passed. Comandos en `mobile/README.md`.
  - 2026-09-18 (bloqueantes B1-B6): rebuild 54.6MB firmado verificado
    (`apksigner verify` OK): consent en registro, jti/denylist + refresh min-15,
    Sentry opt-in (paquete Dart puro; `sentry_flutter` 8.14.2 incompatible con
    Kotlin 2.2 — fija `languageVersion 1.6`), notificaciones locales
    (desugaring `java.time` habilitado), `flutter analyze` 0 issues,
    `flutter test` 43 passed.
  - Pendiente usuario: **respaldar `/home/paul/.mole-android/` + `key.properties`
    fuera de esta máquina**; rebuild con URL real (staging/LAN) para probar en teléfono.
- [ ] `audit-matrix.md` v2 sin claims ❌ abiertos o con plan fechado

## Blocked by

- `02-auth-hs256.md`
- `04-telemetria-edge.md`
- `05-vision.md`
- `06-chat-rag.md`
- `07-mapa-reportes.md`
