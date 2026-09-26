# Issue N-3: Cierre a11y/offline por pantalla

Status: needs-triage
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
(none)
