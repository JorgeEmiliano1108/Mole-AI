# Issue 05: Password-reset sin salida de correo

Status: needs-info
Sev: P0 · Área: backend · Fase: B

## Evidencia
- `settings.py` (448 líneas): cero `DEFAULT_FROM_EMAIL/EMAIL_BACKEND/FRONTEND_BASE_URL`;
  `.env.example` igual. `tasks.py:53-54,112-113` usa `os.getenv(…,localhost:8080)` y
  `settings.DEFAULT_FROM_EMAIL` (cae a `webmaster@localhost` sin SMTP).
- `tasks.py:75-76,129-130` `except → return str` sin retry; `views.py:484-491`
  `try delay() except → warning + 202` (el 202 oculta que el correo nunca sale).

## Problema
El flujo existe pero operacionalmente no envía nada; el 202 miente al usuario.

## Aceptación (según veredicto)
- **Opción SMTP**: proveedor + settings + `.env.example` + retry con backoff + test.
- **Opción 501**: endpoint degradado honesto + nota en docs + issue de seguimiento.
- Bloqueado hasta veredicto del arquitecto (ver PRD).

## Compliance
LFPDPPP: ciclo de vida del dato de recuperación; anti-enumeración se conserva.

## Comments
(none)
