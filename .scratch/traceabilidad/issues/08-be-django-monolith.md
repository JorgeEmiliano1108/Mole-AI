# 08: RF-BE-01: Backend principal en Django

Status: ready-for-human

## Requisito

- **ID:** RF-BE-01
- **Capa:** Backend
- **Tipo:** RF
- **Texto:** El backend principal debe estar construido en Django (Python), sirviendo como enrutador de las peticiones de los usuarios y de sincronización de telemetría.

## Veredicto

✅ CUMPLE — Monolito Django con enrutador `/api/v1/` y endpoints de telemetría.

## Evidencia

- Django 5.2.7: `core_backend/mole_ai_backend/settings.py:6`.
- Enrutador principal: `core_backend/mole_ai_backend/urls.py:44-51`.
- Endpoints de telemetría: `core_backend/apps/core/urls.py:21-26`.
- Vistas de ingesta: `core_backend/apps/core/views.py:233-370`.
- Workers Celery: `core_backend/mole_ai_backend/celery.py`.

## Delta (matriz ideal vs. estado implementado)

Coincide con tesis §4.6.1 y §4.5.3.

## Nota normativa / riesgo

Arquitectura monolítica con workers desacoplados coherente con narrativa 100 % móvil.

## Siguiente paso sugerido

Ninguno; evidencia de auditoría. Cerrar como cumplido tras revisión humana.
