---
name: "[BLOCKED] Migración JWT a HttpOnly Cookie"
about: Dependencia externa del backend para completar Slice 1A
title: "BLOQUEADO: Migración JWT a HttpOnly Cookie + CSRF"
labels: blocked:external, security, frontend
assignees: ''

---

## Descripción

El frontend necesita endpoints del backend `core_backend` para migrar el token JWT de `localStorage` a cookie HttpOnly. Actualmente el token sigue en `localStorage`, accesible vía XSS. Todo el trabajo de sanitización XSS (Slices 1B-1C) queda parcialmente mitigado mientras el token esté en `localStorage`.

## Endpoints Requeridos

### 1. `/auth/login/` — Login con Set-Cookie

- [ ] Emitir `Set-Cookie` con:
  - `HttpOnly`
  - `Secure` (en producción; en dev localhttp omitir Secure)
  - `SameSite=Lax`
  - `Path=/`
  - Nombre: `moleia_jwt` (o el que defina backend)
- [ ] Mantener compatibilidad con `localStorage` durante migración (ventana de coexistencia)
- [ ] Devolver también el token en body de respuesta `{ "token": "..." }` durante la ventana de migración

### 2. `/auth/refresh/` — Refresh Token Rotativo

- [ ] Aceptar cookie HttpOnly como entrada
- [ ] Emitir nueva cookie rotativa en respuesta
- [ ] Política de expiración: access token 15 min, refresh token 7 días (configurable)

### 3. `/csrf/` o meta tag — CSRF Token

- [ ] Endpoint que devuelva `{ "csrfToken": "..." }` o
- [ ] Meta tag `<meta name="csrf-token" content="...">` en HTML servido por Django
- [ ] Token cifrado, enlazado a la sesión

## Plan de Migración

1. **Fase 1 (coexistencia)**: Backend emite cookie + token en body. Frontend prioriza cookie si existe, fallback a `localStorage`. Duración: N días (definir).
2. **Fase 2 (solo cookie)**: Backend deja de devolver token en body. Frontend elimina `localStorage.removeItem('mole_jwt')`.
3. **Rollback**: Si hay errores, revertir a Fase 1 sin downtime.

## Fecha Límite

Sin resolver en **30 días calendario**, implementar plan de contingencia:
- Almacenar token en `sessionStorage` (se limpia al cerrar pestaña)
- Forzar `SameSite=Strict` mediante cookie de sesión HTTP (si backend puede emitirla)

## Contacto

- Frontend: @equipo-frontend
- Backend: @equipo-backend
