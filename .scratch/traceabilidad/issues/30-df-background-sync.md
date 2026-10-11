# 30: RF-DF-02: Sincronización en segundo plano al detectar conectividad

Status: ready-for-agent

## Requisito

- **ID:** RF-DF-02
- **Capa:** Flujo de datos y sincronización
- **Tipo:** RF
- **Texto:** Al detectar conectividad estable a internet, la aplicación debe iniciar un proceso en segundo plano para transmitir la telemetría acumulada y los diagnósticos locales hacia la nube.

## Veredicto

⚠️ PARCIAL — Drenaje de fotos en segundo plano OK; falta sync de telemetría móvil y worker persistente.

## Evidencia

- Drenaje móvil de diagnósticos: `mobile/lib/home_shell.dart:46-62`, `mobile/lib/features/vision/vision.dart:165`.
- Edge node store-and-forward: `edge_node/store_forward_daemon.py:440-472`, `:373-437`.
- No se encontró `WorkManager` ni scheduler persistente para telemetría móvil.

## Delta (matriz ideal vs. estado implementado)

En móvil solo se sincronizan diagnósticos (fotos). `telemetry_cache` no se transmite. El edge node sí hace store-and-forward de telemetría ESP32.

## Nota normativa / riesgo

Transmisión edge→backend usa JWT Bearer con TLS obligatorio en ESP32; daemon tiene default `http://localhost:8000` que en producción debe forzarse a HTTPS vía `EDGE_SYNC_URL`.

## Siguiente paso sugerido

Implementar worker de fondo persistente (ej. WorkManager) para telemetría móvil o ajustar la matriz.
