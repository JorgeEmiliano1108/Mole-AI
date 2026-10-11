# 24: RF-DB-01: SQLite3 local offline

Status: ready-for-human

## Requisito

- **ID:** RF-DB-01
- **Capa:** Bases de datos
- **Tipo:** RF
- **Texto:** Uso de SQLite3 en el dispositivo móvil para almacenar historial de diagnósticos, imágenes en caché y telemetría de forma offline.

## Veredicto

✅ CUMPLE — Esquema SQLite local con telemetría, cola de diagnósticos y consejos offline.

## Evidencia

- Esquema: `mobile/lib/core/offline_db.dart:58-62` (`telemetry_cache`, `diag_queue`, `offline_advice`).
- Operaciones: `mobile/lib/core/offline_store.dart:90-180`.
- Tests: `mobile/test/offline_test.dart:26-182`.

## Delta (matriz ideal vs. estado implementado)

Coincide con tesis §4.3.3-4.3.4. Patrón real Store-and-Forward.

## Nota normativa / riesgo

Datos sensibles en DB cifrada; ver RNF-DB-01.

## Siguiente paso sugerido

Ninguno; evidencia de auditoría. Cerrar como cumplido tras revisión humana.
