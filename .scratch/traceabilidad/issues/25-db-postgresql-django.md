# 25: RF-DB-02: PostgreSQL acoplado a Django

Status: ready-for-human

## Requisito

- **ID:** RF-DB-02
- **Capa:** Bases de datos
- **Tipo:** RF
- **Texto:** Uso de PostgreSQL acoplado a Django para gestionar cuentas de usuario, parcelas y reglas de negocio.

## Veredicto

✅ CUMPLE — PostgreSQL configurado con modelos de usuarios, parcelas y negocio.

## Evidencia

- Configuración: `core_backend/mole_ai_backend/settings.py:147-182`.
- Modelos: `core_backend/apps/authentication/models.py`, `apps/plants/models.py`, `apps/core/models.py`.
- Compose: `infrastructure/docker-compose.yml:170-172` (`pgvector/pgvector:pg16`).

## Delta (matriz ideal vs. estado implementado)

Coincide con tesis §4.6.1.

## Nota normativa / riesgo

Consentimientos LFPDPPP en modelo `User`. `UserPlant` usa `SET_NULL` al borrar.

## Siguiente paso sugerido

Ninguno; evidencia de auditoría. Cerrar como cumplido tras revisión humana.
