# Issue 21: Hardening mobile (casts + cobertura)

Status: ready-for-human
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

## Resolución Wave F1 (2026-10-06, skill `tdd`)
- Mapeo `AppFailure` → jerarquía existente `core/errors.dart` (decisión
  documentada: NO se creó clase nueva; `ApiException` + `apiExceptionFromStatus`
  ya cubren tipado + `statusCode` + mensaje sin PII).
- `auth_repository.dart:23,78` + docstring 501: cuerpo 2xx sin `token` →
  `ApiException` (tests `hardening_casts_test.dart`: login/refresh/501).
- `knowledge_screen.dart:139` → `parseUploadGrant()` en `admin.dart`
  (valida `presigned_url` + `record_id`); `files.first` verificado seguro en
  file_picker v13 (retorna lista no-nula; cancel = vacía; guards nulos
  revertidos por `unnecessary_null_comparison`).
- `offline_db.dart:150-151,192`: fila corrupta → `null`; `COUNT(*)` acepta
  `int64`/`num` (defensa deriva de esquema; sin test nativo posible en
  `flutter_test`, verificado por `analyze` + revisión).
- Extra mismo issue: `map.dart` `Hotspot.tryParse` (entradas inválidas se
  saltan, no tumban el mapa); `plants.dart:206` y `chat.dart:81` ya estaban
  guardados con `is` (verificado, sin cambio).
- Widget tests nuevos `f1_screens_test.dart`: reports (éxito + Reintentar),
  chat (respuesta + disclaimer), weather (preset + coords inválidas sin red),
  diagnosis (estado inicial); map + plant_detail ya cubiertos en `n3_test.dart`.
- Verificación: `flutter test` 151 passed (solo falla `edge_benchmark_test`
  por error preexistente fuera de scope `edge_benchmark.dart:190`
  `Setter not found: '_'`); `flutter analyze` limpio en archivos tocados
  (restan 1 error + 1 info preexistentes en `edge_benchmark*` no tocados).
- Hallazgo derivado (no scope F1, candidato F2): `DiagnosisScreen` desborda
  a 600px de alto (RenderFlex overflow en pantallas chicas).

## Comments
Pendiente validación humana: correr `flutter test` + `flutter analyze` en
máquina del revisor; decidir fix de `edge_benchmark.dart:190` (una línea,
dueño: harness Wave 3).
