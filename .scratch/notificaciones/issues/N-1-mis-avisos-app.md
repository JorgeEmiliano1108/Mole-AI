# Issue N-1: Mis avisos en app (ambos roles)

Status: ready-for-human
Sev: P0 · Área: mobile · Fase: N-1 · Bloqueado por: N-0

## Problema
Botánico y admin no reciben avisos de sus plantas en la app.

## Aceptación
- Centro `Mis avisos`: lista warn/error, pull-to-refresh, vacío declarado,
  reintento; badge no-leídos en NavigationBar (persistido local).
- Polling 30 s solo visible + backoff; local-notify (`notify.dart`) en
  error+warn nuevas con dedup por id; warn/info solo en lista.
- Widget + repository tests (fake client/clock); `analyze` 0 issues.

## Compliance
Sin FCM (decisión); local-notify sin contenido PII sensible.

## Comments
Resuelto: `alerts.dart` (modelo defensivo + repo + `unreadAlertsProvider` Notifier
Riverpod 3), `alerts_screen.dart` (Timer 30 s solo visible + backoff, dedup por
fingerprint, local-notify error/warn, caché offline+chip, `excludeSemantics` para
anuncio único), ruta `/avisos` + drawer con `Badge.count`. Hallazgos: Riverpod 3
sin StateProvider; createTemp cuelga widget tests (ruta falsa); Semantics fusiona
labels hijos (doble lectura → exclude). 9 tests + suite 98/98, analyze 0.

## Resolución Wave F2 (2026-10-06, skills `tdd` + `grill-with-docs`)
- Badge en NavigationBar: `home_shell.dart:alertsDestination(unread)` (5.º
  destino → `context.go('/avisos')`, tabs intactos); drawer conserva el suyo.
  Testeado como función pura (`f2_alerts_weather_test.dart`: con/sin conteo).
- Unread persistido: `UnreadAlertsStore` (prefs `mole_unread_alerts`) +
  `hydrate()` al arrancar el shell; `add/reset` persisten fire-and-forget.
  `alerts_test.dart` usa `setMockInitialValues` (sin channels).
- Dedup por id: `PlantAlert.id` (identidad DERIVADA = fingerprint; el backend
  no emite id — follow-up N-0, documentado en código, no maquillado).
- Verificación: 16 tests (alerts 9 + f2 7) verdes; `analyze` 0 en tocados.
