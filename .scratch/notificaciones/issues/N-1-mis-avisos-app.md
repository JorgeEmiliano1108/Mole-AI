# Issue N-1: Mis avisos en app (ambos roles)

Status: needs-triage
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
(none)
