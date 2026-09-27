# ADR-0008: Brechas entre código y Ficha Metodológica v1 (auditoría)

- **Fecha:** 2026-09-27
- **Estado:** Aceptado (acta de deuda, no cambia código)
- **Contexto:** Auditoría empírica árbol-vs-documento: 11 hallazgos verificados con
  evidencia archivo:línea. El MVP funciona en lo que implementa, pero cinco pilares
  de la ficha no existen en código. Manifiesto único: decide qué se programa en
  código vs qué se renegocia en el documento, sin fragmentar en issues.

## 1. Riesgos de seguridad inmediatos (deuda técnica)
- **Validadores toxicológicos ausentes** (Crítico): disclaimers ≠ validación; sin
  dosis/LD50/Cofepris. Acción: motor de reglas antes de recomendar químicos.
- **Secretos en plano**: `EncryptedCharField` definida jamás instanciada;
  `skip_cert` residual; URI `http` por defecto. Acción: instanciar cifrado + `https`.
- **Higiene móvil**: sin pinning/root-detection/ofuscación (release sin minify,
  fallback a debug.keystore). Acción: pinning + `minify/obfuscate` + Integrity.
- **Prompt injection**: `bleach` declarado sin uso; `user_message` íntegro al LLM.
  Acción: sanitización + tests adversariales.

## 2. Brechas a nivelar en código (plan de acción)
- **7 clases fitosanitarias**: `mole_vision/.../training_pipeline.py` +
  `scripts/train_edge_model.py` son dataset-driven (clases descubiertas, no
  hardcodeadas). Acción: curar dataset de 7 clases → run pipeline → reemplazar
  `plant_mobilenetv2_38.tflite` + `labels.txt` (38→7) → UI resuelve nombres
  (hoy solo `topClass:int`). Esfuerzo Medio (capacidad existente).
- **NOM-059**: regex → tabla oficial SEMARNAT versionada con trazabilidad.
- **RAG**: unificar doble vía de ingesta; alinear dims (Django 1536 vs MS2 1024).
- **MOCK LTR390**: veredicto pendiente (deuda-fase5 issue 11).
- **Métricas Tabla 5**: harness latencia ≤850 ms, gold set alucinaciones,
  `--cov --fail-under=80`, benchmark sync; batería en campo con placa.

## 3. Brechas de alcance a modificar en el documento (renegociación académica)
- **MCP → REST+NVIDIA**: cero imports MCP; arquitectura real REST a MS1/2/3
  (ADR-0004). Reescribir requisito o calendarizar FastMCP (Alto).
- **CRDTs → Store-and-Forward**: `offline_db` sin versiones/vectores; drain =
  POST con reintento probado. Renombrar en ficha.
- **Web Mining fuera del MVP**: sin rutas/scrapers/FAISS; solo pgvector operativo.
  Excluir o especificar pipeline mining→pgvector como fase.
- **pH/EC/riego-PID**: sin hardware ni drivers (pH solo inferencia con mock;
  riego solo `"irrigation_active": False`). Excluir del MVP o planificar HW.
- **Correcciones menores**: modelo `plant_mobilenetv2_38.tflite` 4.6 MB 38 clases
  (no `winner_fp16` 7 clases); suites 46/46 host, 107/107 Flutter.

- **Cumplimiento:** `enforce-compliance` (excepción documentada, no silencio);
  `grill-with-docs` (cada brecha cita archivo:línea); `triage` (§1 bug, §2–3 enhancement).
