# Mole.AI móvil (Flutter) — 7 historias + offline

APK contra el contrato `docs/mobile-contract.md` (fuente de verdad).
Alcance: **auth + especies + telemetría + visión async + chat + mapa + reportes**,
con offline real (caché TTL + cola de diagnósticos con auto-subida).

## Requisitos

- Docker (imagen `ghcr.io/cirruslabs/flutter:stable`). Sin Flutter en el host.
- Backend accesible (dev: `http://10.0.2.2:8000/api/v1/` en emulador Android).

## Comandos (desde la raíz del repo)

```bash
IMG=ghcr.io/cirruslabs/flutter:stable
RUN="docker run --rm -e HOME=/tmp -e PUB_CACHE=/tmp/.pub-cache \
  -v /home/paul/.pub-cache:/tmp/.pub-cache \
  -v /home/paul/.mole-android:/home/paul/.mole-android:ro \
  -v $(pwd)/mobile:/project \
  -w /project $IMG sh -c"

# Análisis + tests
$RUN "flutter analyze; flutter test; chown -R 1000:1000 /project"

# APK release (firmado release; S1 fail-closed sin key.properties)
$RUN "flutter build apk --release \
  --dart-define=API_BASE_URL=https://TU-HOST/api/v1/ \
  --dart-define=MOLE_LAB_CA=1 \
  --obfuscate --split-debug-info=build/debug-info; \
  chown -R 1000:1000 /project"
# Artefacto: mobile/build/app/outputs/flutter-apk/app-release.apk (ignorado por git)
# MOLE_LAB_CA=1: solo laboratorio (confía en lab_ca.pem además del bundle).
# Prod: omitirlo (solo bundle del sistema) + https obligatorio (fail-closed).
```

Firma release (una vez por máquina):
- Keystore fuera del repo: `/home/paul/.mole-android/mole-release.jks` (RSA 2048,
  30 años, SHA-256 `fd3f2b0b…a7574e`). **Respaldarlo fuera de esta máquina**:
  si se pierde, el APK cambia de identidad y los usuarios deben reinstalar.
- `mobile/android/key.properties` (gitignored, `chmod 600`) con
  `storePassword/keyPassword/keyAlias/storeFile`.
- PKCS12 no admite passwords distintos de store y key: ambos iguales.
- El build en Docker necesita montar el keystore:
  `-v /home/paul/.mole-android:/home/paul/.mole-android:ro`.
- Sin `key.properties` el build release FALLA a propósito (S1 MASVS-CODE:
  antes firmaba con debug-keys, clave pública conocida). Dev local usa
  `flutter run` (debug, sin este requisito).

Notas:
- Los contenedores corren como root: el `chown` final devuelve la propiedad.
  Nunca commitear archivos root-owned.
- `API_BASE_URL` solo lleva el host (jamás secrets en el APK).
- Firmado prod: crear keystore release + `key.properties` (ver issue 08); el APK
  actual usa debug-keys del template.

## Estructura

```
lib/
  main.dart                 shell por estado de sesión
  home_shell.dart           bottom nav 6 tabs + drain cola al volver red
  core/                     api_client (Bearer+refresh+trailing slash),
                            session_store (UNA key mole_jwt), errors tipados,
                            offline_store (caché TTL + cola) sobre offline_db
                            (`sqflite`: `telemetry_cache`+`diag_queue`; MRF01),
                            notify (locales),
                            main con runZonedGuarded + Sentry opt-in
  features/auth/            login/registro+consentimiento LFPDPPP/refresh min-15
  features/species/         búsqueda + Nom059Warning obligatorio
  features/plants/          colección + última telemetría (solo lectura)
  features/vision/          foto → edge-first (TFLite) → si duda: POST diagnostics/ → poll
                            modelo `assets/models/` (stand-in documentado; MRF02)
  features/chat|map|reports chat gateway, flutter_map+hotspots, MS3 presigned
test/                       43 tests (api_client, auth, species, plants, vision, chat/map/reports, offline, ux, notify)
```

## Checklist publicación (Play)

- `API_BASE_URL` prod con HTTPS (banderazo `--dart-define`, jamás http en prod).
- Keystore respaldado fuera de la laptop + `key.properties` 600 (nunca en git).
- `version:` en `pubspec.yaml` bump por release (`flutter.versionCode/Name` lo heredan).
- `targetSdk` = default del SDK Flutter (auditable en `flutter doctor`; fijar manual
  solo si Play lo exige por encima del default).
- Data Safety + privacy policy URL: servir `GET /privacy/` de Django en el dominio
  (plantilla `core_backend/templates/privacy.html`, LFPDPPP) y declarar recolección
  (cuenta, plantas, telemetría, fotos, LFPDPPP/consentimiento).
- Notificaciones: solo locales (`flutter_local_notifications`, permiso
  POST_NOTIFICATIONS perezoso); sin FCM por decisión (ver issue 08).
- Observabilidad: `--dart-define=SENTRY_DSN=...` (sin DSN = no-op, sin PII).
