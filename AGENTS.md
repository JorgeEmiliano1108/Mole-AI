# AGENTS.md — Mole.AI

## Agent skills

### Issue tracker

Local markdown under `.scratch/<feature>/` (solo project, sin remoto requerido). See `docs/agents/issue-tracker.md`. Migración a GitHub Issues (`gh` CLI, repo `JorgeEmiliano1108/Mole-AI`) al congelar MVP Flutter.

### Triage labels

Canónicos `needs-triage / needs-info / ready-for-agent / ready-for-human / wontfix` como `Status:` en cada issue. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context. See `docs/agents/domain.md`. Glosario: `CONTEXT.md` raíz. Decisiones: `docs/adr/`.

## Skills activas (skills-main/)

Core auditoría/MVP: `enforce-compliance` (SKILL_NORMATIVE.md, guardrails LFPDPPP/IFT-016/NOM-059, siempre antes de tocar auth/telemetría/uploads), `grill-with-docs`, `improve-codebase-architecture`, `tdd`, `diagnose`, `to-prd`, `to-issues`, `triage`, `zoom-out`, `setup-matt-pocock-skills` (ya ejecutado: tracker local + labels default + single-context).

## Guardrails de código (resumen enforce-compliance)

- Telemetría ESP32 solo con TLS; sin handshake → Fail-Safe + SQLite Store&Forward (`edge_node/store_forward_daemon.py`), nunca texto plano.
- Rutas de archivos usuario solo con `django.utils._os.safe_join`, nunca `os.path.join`/f-strings (`apps/ai_models/views.py`, `apps/core/views.py:diagnostic_view`).
- Especies NOM-059 → disclaimer obligatorio `bg-red-500/10 border-red-500/30` en web y Flutter.
- Criterio aceptación: linters sin warnings + SonarQube 0 Blocker en archivos tocados.
