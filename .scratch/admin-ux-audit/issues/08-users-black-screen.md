# Issue 08 — Pantalla negra en /admin/usuarios en dispositivo

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — `UsersScreen` envuelto en `Scaffold`; smoke test en Samsung SM-A336M muestra AppBar "Usuarios" y lista de 4 usuarios; `flutter test` 137/137; `flutter analyze` limpio.
- **Category:** bug
- **Priority:** high
- **Skill:** diagnose + tdd

## Problema
En el Samsung SM-A336M la ruta `/admin/usuarios` se renderiza como pantalla negra y el árbol de semántica está vacío (UIAutomator: 7 nodos genéricos, 0 con texto). No ocurre en las otras 5 pantallas admin.

## Evidencia
- `mobile/lib/features/admin/users_screen.dart:143` retorna `SafeArea(child: Padding(...))` **sin `Scaffold` / `Material`**.
- Comparación: `audit_screen.dart`, `knowledge_screen.dart` y `system_events_screen.dart` envuelven su contenido en `Scaffold`.
- Los widget tests pasan porque `mobile/test/admin_a11y_test.dart:35` envuelve `UsersScreen` en `MaterialApp > Scaffold(body:)` — el seam de test es demasiado superficial y oculta la falta de ancestro `Material`.
- Logcat del proceso muestra errores `gralloc4` de alloc de buffers al momento de la navegación (pista secundaria de fallo de render).
- curl confirma que `GET /api/v1/admin/users/` responde 200 con 4 usuarios; el backend no es la causa.

## Hipótesis rankeadas
1. **Falta `Scaffold`/`Material`** (más probable). Predicción: envolver `UsersScreen` en `Scaffold` hace que aparezcan los controles y la semántica.
2. **Impeller/Vulkan** no puede allocar buffer para este widget tree. Predicción: `flutter run --no-enable-impeller` renderiza.
3. **Excepción en build** es tragada por la capa de render. Predicción: `flutter run` muestra el error en consola.

## Solución
- Envolver `UsersScreen` en `Scaffold` con `AppBar(title: Text('Usuarios'))`.
- Aprovechar para unificar el estado de error con `AdminErrorPanel` (consistente con Knowledge/Auditoría).
- Asegurar que el diseño sea responsivo y amigable (ISO 25010/25000: apropiación, accesibilidad, estética, operabilidad): etiquetas claras, botones ≥48 dp, feedback de carga/error/vacío, Semantics.

## Tests
- Regresión en `admin_a11y_test.dart` o nuevo `admin_users_integration_test.dart`: pumpear `UsersScreen` como lo monta el router (sin `Scaffold` externo) y verificar que renderiza al menos el campo de búsqueda y el título.
- `flutter test` completo debe seguir pasando.

## Criterio de aceptación
- Loop adb (launch → login → Panel admin → Usuarios → uiautomator dump) muestra nodos de texto como "Buscar usuario o correo".
- `flutter analyze` limpio y `flutter test` verde.
