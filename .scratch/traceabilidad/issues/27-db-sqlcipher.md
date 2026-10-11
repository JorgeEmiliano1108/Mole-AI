# 27: RNF-DB-01: SQLCipher AES-256 para SQLite local

Status: ready-for-human

## Requisito

- **ID:** RNF-DB-01
- **Capa:** Bases de datos
- **Tipo:** RNF
- **Texto:** La base de datos local (SQLite3) debe implementarse mediante SQLCipher, asegurando cifrado AES-256 para evitar el robo de datos en caso de compromiso del dispositivo.

## Veredicto

✅ CUMPLE — SQLCipher AES-256 con clave en keystore.

## Evidencia

- Dependencia: `mobile/pubspec.yaml:49` (`sqflite_sqlcipher`).
- Diseño S1: `mobile/lib/core/offline_db.dart:7-12, 47-73, 82-126`.
- Clave en secure storage: `mobile/lib/core/offline_store.dart:20-52`.
- Tests: `mobile/test/s1_test.dart:22-45`.

## Delta (matriz ideal vs. estado implementado)

Coincide con tesis §4.3.3. Residual documentado: JPEG en cola sin cifrado de fichero.

## Nota normativa / riesgo

Cumple OWASP MASVS-STORAGE y LFPDPPP (cifrado en reposo).

## Siguiente paso sugerido

Ninguno; evidencia de auditoría. Cerrar como cumplido tras revisión humana.
