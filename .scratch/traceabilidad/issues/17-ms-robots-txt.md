# 17: RNF-MS-02: Cumplimiento ético robots.txt

Status: ready-for-human

## Requisito

- **ID:** RNF-MS-02
- **Capa:** Microservicios y Web Mining
- **Tipo:** RNF
- **Texto:** El proceso de recolección de datos automatizada (scraping) debe respetar estrictamente los protocolos robots.txt de las fuentes científicas y gubernamentales.

## Veredicto

❌ NO IMPLEMENTADO — No hay scrapers ni parser de robots.txt.

## Evidencia

- No existen módulos de scraping, crawler ni referencias a `robots.txt`, `OMRI`, `NOM-037`.
- ADR-0008 confirma ausencia de scrapers.

## Delta (matriz ideal vs. estado implementado)

Discrepancia estructural: sin Web Mining no hay recolección automatizada.

## Nota normativa / riesgo

La ausencia de scraping evita una brecha ética activa, pero constituye deuda de cumplimiento para cuando se reintroduzca.

## Siguiente paso sugerido

Decisión arquitectónica: si se implementa Web Mining, incluir parser de robots.txt, rate limiting y registro de crawl desde el diseño.
