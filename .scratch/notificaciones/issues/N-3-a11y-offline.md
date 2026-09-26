# Issue N-3: Cierre a11y/offline por pantalla

Status: ready-for-human
Sev: P1 · Área: mobile · Fase: N-3

## Problema
Mapa severidad solo-color; plant_detail sin reintento ni aviso offline;
dashboard weather silencioso; knowledge sin polling de indexado.

## Aceptación
- Severidad color+etiqueta; mensaje vacío en mapa; reintento+chip offline donde
  falte; polling de estado knowledge.
- Widget/a11y tests por fix (prior art: admin_a11y_test); suite verde.

## Compliance
RNF-UX01/02 del plan (AA, 48dp, sin info solo-color, offline declarado).

## Comments
Resuelto: mapa con Semantics por marcador (especie+severidad en texto) y mensaje
de vacío; plant_detail con reintento + chip offline (usa el flag de latestCached
que se descartaba) + error con liveRegion; knowledge con polling transitorio
(PENDING/UPLOADING/UPLOADED/INDEXING, máx 6 con backoff) + helper testeable.
5 tests nuevos; suite 107/107, analyze 0.
