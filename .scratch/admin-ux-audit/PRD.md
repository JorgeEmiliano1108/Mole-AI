# PRD — Auditoría UX/UI y funcionalidad del módulo Admin

## Contexto
El usuario reportó que "algunas vistas del admin marcan error" al probar la app en un Samsung SM-A336M contra el backend local. La auditoría de solo-lectura identificó la causa raíz y varios gaps UX/UI/a11y.

## Objetivo
Corregir los errores funcionales del módulo Admin en la app móvil y elevar la calidad UX/UI de las pantallas administrativas, manteniendo cobertura de tests ≥80% en backend, linters limpios y cumplimiento normativo.

## Alcance (incluido)
- S1: Trailing slash en endpoints admin (`admin/statistics`, `admin/live-alerts`, `admin/system-events`, `admin/audit-log`, `admin/reports/*`).
- S2: Campo `record_id` en listados de training (`training/documents/` e `images/`).
- S3: Restringir listados de training a `IsAdminUser` (enforce-compliance).
- S4: Patrón unificado de error + retry en Knowledge y Auditoría.
- S5: Feedback positivo (SnackBar) tras mutaciones en Usuarios.
- S6: Mejoras a11y: Semantics en listas Users/Knowledge, indicador no-solo-color para inactivo, fontSize escalable y colores del scheme en Fallas.
- S8: Alinear openapi.yml DELETE users a 200 (o cambiar backend a 204 si se prefiere).

## Fuera de alcance (fase futura)
- Paginación completa de Auditoría (se documenta el gap, no se implementa).
- Internacionalización (l10n); se mantiene español hardcoded.
- Rediseño visual profundo de charts.

## Criterios de aceptación transversales
1. `pytest --cov=apps --cov-fail-under=80` pasa.
2. `flutter test` pasa (134 existentes + nuevos).
3. `ruff` y `flutter analyze` limpios en archivos tocados.
4. SonarQube 0 Blocker en archivos modificados.
5. curl loop contra `http://127.0.0.1:8080/api/v1/` devuelve 401 (no 404) para los endpoints admin que la app consume.
6. Rebuild + reinstall en el Samsung con la última APK; validación manual de Métricas, Auditoría y Centro de fallas.

## Estado
- Implementación de S1-S6 y S8 completada el 2026-09-30.
- Issues 08-10 completadas el 2026-09-30.
- `flutter test`: 137/137 pasan.
- `flutter analyze`: limpio en todo el proyecto.
- Backend: tests de admin y training pasan; ruff limpio.
- curl loop contra backend local: 200/401 en todos los endpoints admin consumidos.
- APK debug reinstalada en Samsung SM-A336M; smoke test en vivo exitoso para Panel admin, Métricas, Auditoría y Usuarios.

## Decisiones clave
- Fix S1 por vía backend: se agrega `/` final a las rutas admin para respetar el contrato §0 del cliente (`trailing slash obligatorio`).
- S3 se ejecuta bajo `enforce-compliance` antes de tocar permisos de uploads/entrenamiento.

## Issues vinculados
- `.scratch/admin-ux-audit/issues/01-*.md` … `07-*.md`
