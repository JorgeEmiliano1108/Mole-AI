# Issue 21: Hardening mobile (casts + cobertura)

Status: ready-for-agent
Sev: P1 · Área: mobile · Fase: F

## Evidencia
- Casts inseguros: `auth_repository.dart:23,78` `body['token'] as String` (truena
  en 400/500); `knowledge_screen.dart:98` `req['presigned_url'] as String`;
  `offline_db.dart:69-70` `as String` (null → `TypeError`); `files.first` con
  `FilePickerResult?` nullable.
- Sin tests: reports/map/chat/weather/diagnosis/plant_detail (solo auth/users/
  knowledge/forgot + decoder BLE tienen cobertura).

## Problema
`TypeError` en runtime en vez de error tipado; pantallas sin red de seguridad.

## Aceptación
- Parseo defensivo con errores tipados (`AppFailure`) en los 4 puntos + widgets
  tests de las pantallas listadas; suite 100% verde; `analyze` 0 issues.

## Compliance
Calidad ISO/IEC 25001; sin PII en mensajes de error al usuario.

## Comments
(none)
