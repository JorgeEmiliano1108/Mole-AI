# Datasheet — PlantVillage color (entrenamiento MRF02)

- **Fuente**: `spMohanty/PlantVillage-Dataset` (GitHub, commit `7f7ecc7`), vía
  `plant_village.py` (licencia y citación en `CITATION.cff` del dataset).
  Copia local: `/home/paul/.mole-datasets/PlantVillage/` (fuera del repo).
- **Split usado**: `raw/color/` — 54,305 JPG a color, fondo de laboratorio uniforme.
- **Clases**: 38 (calzan con `models/labels.json:0-37`; entrada `38` normalizada
  a sentinela `Desconocida`).
- **Desbalance**: min 152 (`Potato___healthy`) → max 5,507 (`Orange___Haunglongbing`);
  P2 usa `class_weight` balanceado + métrica F1-macro (no accuracy cruda).
- **Limitación conocida (revisión 2026-09-19)**: fondos uniformes de laboratorio
  → riesgo de caída en campo. Mitigación P1: mezcla de fondos ruidosos/de campo
  + guía ROI en app (`DiagnosisScreen`); holdout de campo como gate (no solo lab).
- **Preproceso canónico**: 224×224 RGB, `[-1,1]` (idéntico a `preprocessJpeg` del
  APK; test testigo en P1). No se commitean imágenes al repo.
