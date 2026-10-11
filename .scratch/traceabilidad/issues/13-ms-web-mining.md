# 13: RF-MS-01: Microservicio independiente de Web Mining

Status: ready-for-human

## Requisito

- **ID:** RF-MS-01
- **Capa:** Microservicios y Web Mining
- **Tipo:** RF
- **Texto:** Un microservicio independiente debe ejecutar el Web Mining para la extracción de manuales agronómicos, NOM-037-FITO y bases de datos OMRI.

## Veredicto

❌ NO IMPLEMENTADO — Web Mining excluido del MVP.

## Evidencia

- `microservices/` solo contiene `mole_chat`, `mole_report`, `mole_vision`, `esp32_node`.
- ADR-0008: 'Web Mining fuera del MVP: sin rutas/scrapers/FAISS; solo pgvector operativo.'
- Tesis §4.2.1 y §4.6.1 documentan la exclusión.

## Delta (matriz ideal vs. estado implementado)

Discrepancia estructural: la matriz ideal exige Web Mining; el estado implementado lo excluyó del MVP.

## Nota normativa / riesgo

Al no existir recolección automatizada, se evita riesgo ético de scraping; su reintroducción requerirá parser de `robots.txt` y throttling.

## Siguiente paso sugerido

Decisión arquitectónica: incluir Web Mining en fase posterior o actualizar ficha metodológica/tesis para reflejar que queda fuera del MVP.
