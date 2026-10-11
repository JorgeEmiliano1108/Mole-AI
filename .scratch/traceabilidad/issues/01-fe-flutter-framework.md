# 01: RF-FE-01: Framework Flutter y compatibilidad Android

Status: ready-for-human

## Requisito

- **ID:** RF-FE-01
- **Capa:** Frontend
- **Tipo:** RF
- **Texto:** La aplicación debe estar desarrollada en el framework Flutter, garantizando compatibilidad multiplataforma (Android prioritariamente para el MVP).

## Veredicto

✅ CUMPLE — El proyecto es Flutter y el target principal es Android.

## Evidencia

- `mobile/pubspec.yaml:31-32` declara `flutter: sdk: flutter`.
- `mobile/android/settings.gradle.kts` y `mobile/android/app/build.gradle.kts` confirman target Android.
- `mobile/pubspec.yaml:86-87` empaqueta el modelo TFLite para el bundle APK.
- `mobile/test/edge_ai_test.dart:84-88` valida que el modelo esté declarado.

## Delta (matriz ideal vs. estado implementado)

Coincide con tesis §4.3.1. iOS/web no son prioridad del MVP.

## Nota normativa / riesgo

OWASP MASVS-PLATFORM: uso de APIs Flutter estándar; sin canales nativos custom innecesarios.

## Siguiente paso sugerido

Ninguno; evidencia de auditoría. Cerrar como cumplido tras revisión humana.
