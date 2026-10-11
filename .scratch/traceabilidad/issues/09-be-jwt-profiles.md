# 09: RF-BE-02: Autenticación JWT y gestión de perfiles/parcelas

Status: ready-for-human

## Requisito

- **ID:** RF-BE-02
- **Capa:** Backend
- **Tipo:** RF
- **Texto:** Debe implementar un sistema de autenticación de usuarios mediante tokens JWT y gestionar los perfiles de los agricultores y parcelas.

## Veredicto

✅ CUMPLE — JWT HS256 local, perfiles y parcelas implementados.

## Evidencia

- Autenticación JWT local: `core_backend/apps/authentication/infrastructure/local_jwt_auth.py:13-115`.
- Login: `core_backend/apps/authentication/views.py:289-359`.
- Refresh: `core_backend/apps/authentication/refresh.py:19-49`.
- Perfil de usuario: `core_backend/apps/authentication/views.py:30-107`.
- Parcelas (`UserPlant`): `core_backend/apps/plants/models.py:82-116`, `views.py:117-152`.

## Delta (matriz ideal vs. estado implementado)

Coincide con tesis §4.3.2 y §4.6. Supabase autenticación está deshabilitada como método canónico.

## Nota normativa / riesgo

LFPDPPP: consentimiento explícito en modelo `User`; minimización de claims JWT (`sub`, `role`).

## Siguiente paso sugerido

Ninguno; evidencia de auditoría. Cerrar como cumplido tras revisión humana.
