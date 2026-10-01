# Issue 06 — Mejoras de accesibilidad en listas admin

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — Semantics en filas Users/Knowledge, badge Inactivo visible, colores del ColorScheme en Fallas; `flutter test` y `flutter analyze` limpios.
- **Priority:** medium
- **Skill:** tdd

## Problema
- Usuarios: estado inactivo se comunica solo por color del icono.
- Usuarios / Knowledge: filas de lista sin `Semantics` label.
- Centro de fallas: `fontSize: 12` fijo y `Colors.orange` fuera del `ColorScheme` (contraste).

## Evidencia
- `mobile/lib/features/admin/users_screen.dart:191-199`
- `mobile/lib/features/admin/knowledge_screen.dart:200-213`
- `mobile/lib/features/admin/system_events_screen.dart:14-24,99-103`

## Solución
- Añadir `Semantics` wrapper por fila en Users y Knowledge.
- Añadir texto/badge "Inactivo" visible junto al icono en Users.
- Reemplazar `fontSize: 12` por `Theme.of(context).textTheme.labelSmall`.
- Reemplazar `Colors.orange` por `colorScheme.warning`/`errorContainer` o color del tema.

## Tests
- `admin_a11y_test.dart` ya cubre tamaños y modo oscuro; extender con Semantics labels.

## Criterio de aceptación
- `flutter test` pasa con tests de Semantics.
- `flutter analyze` limpio.
