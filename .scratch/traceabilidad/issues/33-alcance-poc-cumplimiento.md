# Issue 33: Alcance PoC de cumplimiento normativo (deuda explícita)

Status: needs-info
Sev: P2 · Área: compliance/docs · Fase: post-MVP

## Declaración honesta (2026-10-04)
El sistema implementa mecanismos reales (SafetyValidator fail-closed,
AuditLog inmutable, HMAC-SHA256, SQLCipher) pero sobre **Catálogos Semilla
Demostrativos** y con cobertura parcial. Ninguna afirmación de esta issue
sustituye asesoría legal; es deuda técnica explícita, no cumplimiento.

## Carencias documentadas (con evidencia)
1. **Catálogo NOM-059 semilla**: `docs/safety/nom059_species.json` trae 2 de
   miles de especies oficiales. Pendiente: ingesta versionada de la lista
   SEMARNAT + pipeline de actualización (ADR-0008 lo registra como deuda).
2. **Catálogo NOM-037 semilla**: `docs/safety/agrochemical_limits.json` trae 2
   sustancias marcadas "Ejemplo de esqueleto validable"; sin LD50/MRL; NOM-037
   ni aparece en `safety_rules.yaml`. Pendiente: dataset regulatorio real.
3. **Sin rotación HMAC**: `ANONIMIZACION_KEY` estática; `KeyProvider` sin
   implementar (ver `anonimizacion/02-key-provider-strategy.md`).
4. **Sin Web Mining / Codex / OMRI**: RAG = PDFs manuales → `rag_knowledge_chunks`
   (descarto explícito ADR-0008). Pendiente solo si el SaaS lo exige.
5. **Sin mTLS interno**: MS se comunican por HTTP plano (aceptado hasta Fase 2).
6. **Silent-compliance aplicado**: UX sin menciones normativas (ver
   `apps/core/services/safety_presentation.py`); PDFs conservan disclaimer
   genérico como escudo. Consentimiento LFPDPPP y privacy.html intactos por
   obligación legal de informar.

## Criterio de salida
Cada punto requiere su propio issue de implementación con fuente regulatoria
citada y tests de cobertura del catálogo antes de afirmar cumplimiento.
