# Issue 05 — Feedback positivo en mutaciones de Usuarios

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — SnackBar tras cambio de rol y activación/desactivación; tests de widget pasan.
- **Priority:** medium
- **Skill:** tdd

## Problema
Al cambiar rol o activar/desactivar un usuario, la pantalla recarga silenciosamente. No hay confirmación de éxito para el administrador.

## Evidencia
- `mobile/lib/features/admin/users_screen.dart:91-127`

## Solución
Mostrar `SnackBar` con mensaje de confirmación tras PATCH exitoso ("Rol actualizado", "Usuario desactivado", etc.).

## Tests
- Widget test: tras tocar opción de rol, aparece SnackBar con texto esperado.

## Criterio de aceptación
- Usuario recibe feedback visual inmediato tras mutación exitosa.
