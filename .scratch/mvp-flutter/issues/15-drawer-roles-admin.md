# 15 — Drawer, roles y panel admin

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

`HomeShell` → `Scaffold(drawer: AppDrawer)` + `NavigationBar` 4 destinos (Inicio/Plantas/Clima/Diagnóstico); resto en drawer; sección admin solo `isAdmin` con `RoleGuard` + redirect. Nuevas: Inicio dashboard, detalle planta, Clima (repos existentes + selector ubicación), historial diagnósticos, visor `ChatSource`. Admin: Métricas (`fl_chart` + `MetricsRepository`), Knowledge (PUT presigned + confirm + polling), Usuarios (CRUD issue 16). `AuthState.isAdmin` (`role admin|superuser`).

## Acceptance criteria

- [ ] Drawer por rol testeado (admin ve sección, user no)
- [ ] 4 destinos + pantallas nuevas con tests widget (incl. a11y: Semantics, 48dp, dark, escalado)
- [ ] Admin metrics/knowledge/users contra backend real (staging)

## Blocked by

- `14-portal-publico.md`
- `16-password-reset.md` (endpoints admin usuarios)
