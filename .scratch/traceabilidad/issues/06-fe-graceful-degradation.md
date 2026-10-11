# 06: RNF-FE-02: Graceful Degradation y offline-first

Status: ready-for-human

## Requisito

- **ID:** RNF-FE-02
- **Capa:** Frontend
- **Tipo:** RNF
- **Texto:** La aplicación debe aplicar Graceful Degradation; si se pierde la conexión a internet, la UI debe seguir funcionando mostrando datos cacheados y permitiendo la inferencia convolucional local sin colapsar.

## Veredicto

✅ CUMPLE — Arquitectura offline-first robusta.

## Evidencia

- SQLCipher AES-256: `mobile/lib/core/offline_db.dart`.
- Cola de fotos: `mobile/lib/core/offline_store.dart:122-142`.
- Drenaje automático al recuperar red: `mobile/lib/home_shell.dart:47-62`.
- Inferencia local: `mobile/lib/features/vision/edge_ai.dart`.
- PVU routing: `mobile/lib/pvu/routing.dart:51-65`.
- Tests: `mobile/test/offline_test.dart`, `mobile/test/pvu_routing_test.dart`, `mobile/test/edge_ai_test.dart`.

## Delta (matriz ideal vs. estado implementado)

Totalmente alineado con tesis §4.3.3-4.3.4, §4.4.2-4.4.3. Patrón real Store-and-Forward.

## Nota normativa / riesgo

OWASP MASVS-STORAGE + LFPDPPP: DB cifrada + clave en `flutter_secure_storage`. Residual documentado: JPEG en cola sin cifrado de fichero.

## Siguiente paso sugerido

Ninguno; evidencia de auditoría. Cerrar como cumplido tras revisión humana.
