# 10: RF-BE-03: Endpoints seguros para conciliación offline

Status: ready-for-human

## Requisito

- **ID:** RF-BE-03
- **Capa:** Backend
- **Tipo:** RF
- **Texto:** Debe proporcionar endpoints seguros para recibir y conciliar la información generada en modo offline por los dispositivos móviles.

## Veredicto

✅ CUMPLE — Endpoints `batch/`, `edge-batch/`, `sync/batch/` con autenticación de dispositivo.

## Evidencia

- URLs: `core_backend/apps/core/urls.py:23-26`.
- Vistas: `core_backend/apps/core/views.py:200-217`, `:233-275`, `:278-369`.
- Autenticación dispositivo: `core_backend/apps/core/views.py:120-148` (`DeviceBearerPermission`).
- Lógica compartida ACID: `core_backend/apps/core/services/edge_ingest.py:24-100`.

## Delta (matriz ideal vs. estado implementado)

Patrón real Store-and-Forward documentado en ADR-0008. Coincide con tesis §4.3.4 y §4.5.3.

## Nota normativa / riesgo

Endpoints con autenticación JWT/Hardware y denegación 401. Legacy `sensor-data/batch/` usa `HardwareAPIKeyAuthentication` (dual-stack aceptado).

## Siguiente paso sugerido

Ninguno; evidencia de auditoría. Cerrar como cumplido tras revisión humana.
