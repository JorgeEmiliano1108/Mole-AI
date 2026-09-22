# 14 — Portal público + autenticación móvil

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Portal público sin login (hero objetivo/filosofía, buscador especies con caché, clima demo) con CTAs Entrar/Crear cuenta; `go_router` + `MaterialApp.router` con redirect por `AuthStatus`+rol; login/registro/consent existentes + `forgot-password` (request/confirm, anti-enumeración) + validación email/longitud; modo invitado ampliando `ApiClient._isPublicAuth` a `plants/search/`, `weather/current/`, `health/`.

## Acceptance criteria

- [ ] Invitado navega portal + fichas + NOM-059 sin token
- [ ] Flujo completo registro→consent→login→portal desbloqueado
- [ ] Forgot-password E2E contra backend (request siempre 202, confirm rota password)
- [ ] `flutter analyze` 0 issues + widget tests (portal, login validación, consent)

## Blocked by

- `16-password-reset.md` (endpoints backend)
- `18-curaduria-flora.md` (contenido verídico del portal)
