# 11: RNF-BE-01: ORM y protección contra inyección SQL

Status: completed

## Requisito

- **ID:** RNF-BE-01
- **Capa:** Backend
- **Tipo:** RNF
- **Texto:** Debe utilizar un Object-Relational Mapper (ORM) para interactuar con la base de datos, abstrayendo las consultas SQL directas y eliminando el riesgo de inyecciones SQL.

## Veredicto

✅ CERRADO PARA MVP — `admin_stats_view` ya usa ORM; refresh de MV documentado como excepción.

## Evidencia

- Django ORM en modelos y vistas (`apps/core/models.py`, `apps/plants/views.py`, etc.).
- `admin_stats_view`: ahora consulta el modelo no gestionado `AdminStats` (`apps/core/models.py:351-365`) en lugar de `cursor.execute`.
- `REFRESH MATERIALIZED VIEW CONCURRENTLY admin_stats` (`core_backend/apps/core/tasks.py:77-80`) sigue siendo SQL fijo por ser DDL; no es inyectable y está documentado como excepción arquitectónica.
- No se encontraron consultas dinámicas con interpolación de entrada de usuario.

## Delta (matriz ideal vs. estado implementado)

La superficie de SQL directo productivo se reduce a DDL de mantenimiento programado (MV refresh). La abstracción ORM cubre todas las consultas dinámicas de API.

## Nota normativa / riesgo

Riesgo de inyección SQL mitigado: solo queda sentencia fija sin entrada de usuario.

## Siguiente paso sugerido

- Si la MV se vuelve dinámica o parametrizada, reevaluar y migrar a ORM/aggregaciones.
- Documentar excepción formal en ADR de deuda técnica (Wave 4).
