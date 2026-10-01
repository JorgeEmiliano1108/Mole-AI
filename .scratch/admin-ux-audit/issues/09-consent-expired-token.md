# Issue 09 — Consentimiento bloqueado con token expirado

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — `AuthController.grantConsent` maneja `UnauthorizedException` limpiando sesión y redirigiendo a login; test de widget pasa; no se debilita el gate de consentimiento.
- **Category:** bug
- **Priority:** high
- **Skill:** enforce-compliance + tdd

## Problema
Cuando el token almacenado expira y la app se reinicia, la pantalla `/consentimiento` muestra el mensaje "Token has expired." y el botón "Acepto el uso de mis datos" no avanza. El usuario queda atrapado sin poder llegar al login.

## Evidencia
- Reproducido tras `adb shell pm clear` + login + force-stop con token expirado.
- El `redirect` de `app_router.dart:59` envía a `/consentimiento` cuando `AuthStatus.needsConsent`.
- Si el token ya expiró, el endpoint de aceptación de consentimiento devuelve 401/403; la UI no redirige a login.

## Solución
- Detectar token expirado en el flujo de consentimiento.
- Limpiar la sesión y redirigir a `/login` para que el usuario vuelva a autenticarse; el consentimiento se solicitará de nuevo tras un login exitoso.
- En la UI de consentimiento mostrar un mensaje claro y un botón alternativo "Ir a iniciar sesión" para cumplir con usabilidad ISO 25000 (control del usuario, prevención de errores).

## Guardrails (enforce-compliance)
- No se debe saltar nunca el consentimiento LFPDPPP.
- Un usuario sin consentimiento válido debe seguir sin poder acceder a funcionalidad protegida.
- El fix solo cambia el *camino* hacia el login, no debilita el gate.

## Tests
- Widget/integración: simular `AuthStatus.needsConsent` con token expirado → se redirige a `/login`.
- Test negativo: usuario autenticado sin consent sigue siendo redirigido a `/consentimiento` (no se debilita el gate).

## Criterio de aceptación
- Tras expirar el token, la app permite al usuario llegar a login sin quedar atrapado.
- `flutter test` verde.
- No regresión en cobertura de consentimiento.
