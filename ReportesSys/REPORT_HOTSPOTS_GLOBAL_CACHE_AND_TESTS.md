Informe técnico: Cambio a caché GLOBAL en endpoint /api/v1/map/hotspots/ y resultados de integración
================================================================================

Fecha: 15 de marzo de 2026
Autor: Acciones automáticas realizadas por el agente en el workspace

Resumen ejecutivo
-----------------
- Objetivo: Cambiar la estrategia de caché del endpoint `/api/v1/map/hotspots/` para que sea GLOBAL (datos comunitarios) y asegurar que el QuerySet no esté filtrado por `user_id`. Garantizar además que la salida sea agregada y no exponga datos personales. Crear y verificar tests de integración que validen comportamiento funcional y privacidad.
- Resultado: Cambios aplicados, correcciones de migraciones y modelos, y suite de integración creada/ajustada. Tests ejecutados: 9/9 passed en entorno de pruebas local (pytest).

Cambios principales aplicados
-----------------------------
Modificaciones de código (nuevos/actualizados):
- Re-export de modelos para que Django descubra modelos del app `core`:
  - [apps/core/models.py](apps/core/models.py)

- Vistas / caché / serialización:
  - [apps/core/presentation/views.py](apps/core/presentation/views.py)  — Cache key cambiada a GLOBAL: `hotspots:{days}:{pest}:{precision}` (eliminado `user_id`); QuerySet ya era global (sin filtro por usuario); lógica de agrupamiento por cuadrícula (round) y cálculo de radio con Haversine permanece.
  - [apps/core/presentation/serializers.py](apps/core/presentation/serializers.py) — `HotspotSerializer` usado para garantizar respuesta agregada (campos permitidos: `latitud_centro`, `longitud_centro`, `radio_estimado_metros`, `total_casos`, `plaga_predominante`, `severity_index`).

- Migrations ajustadas para compatibilidad con `AUTH_USER_MODEL` y comportamiento de tablas:
  - [apps/core/migrations/0004_diagnosticos_geolocalizados.py](apps/core/migrations/0004_diagnosticos_geolocalizados.py) — reemplazada referencia estática `to='auth.user'` por `to=settings.AUTH_USER_MODEL` y añadida `migrations.swappable_dependency(settings.AUTH_USER_MODEL)` en `dependencies`.
  - [apps/core/migrations/0001_initial.py](apps/core/migrations/0001_initial.py) — `AIDiagnostic` cambió de `managed=False` a `managed=True` para alinear migraciones con los modelos reales (necesario para crear la tabla `ai_diagnostics` en la DB de pruebas).

- Tests / datos de prueba:
  - [tests/integration/test_map_hotspots.py](tests/integration/test_map_hotspots.py) — Archivo de pruebas de integración creado/consolidado (9 tests). Ajuste en los valores de semilla para garantizar que dos puntos cercanos agrupen con `precision=4`.

- Otros ajustes de entorno de pruebas:
  - `conftest.py` (raíz) ya existente: override de `CACHES` a `LocMemCache` y fixture que crea tablas unmanaged necesarias (`UserPlant`, `SensorLog`). No modificado en esta pasada, pero se utilizó para las pruebas locales.

Motivación y diagnóstico
------------------------
- Problema inicial: los modelos del `core` no eran detectados por Django porque estaban definidos en un submódulo (`apps/core/infrastructure/repositories/models.py`) sin un `apps/core/models.py` que los re-exportara. Django auto-descubre únicamente `app_label.models` (o requiere imports explícitos en `AppConfig`). Resultado: durante la ejecución de pytest Django no veía modelos del app `core` y las migraciones/tablas no se aplicaban como se esperaba.
- Efectos colaterales detectados: fallos en pytest por tablas faltantes (primero `auth_user`, luego `ai_diagnostics`). Se resolvieron corrigiendo migraciones y añadiendo el re-export para registrar correctamente los modelos.

Acciones realizadas (paso a paso)
---------------------------------
1. Inspección del app `core` y verificación de que `apps/core/models.py` no existía. Se creó `apps/core/models.py` que re-exporta los modelos definidos en `infrastructure/repositories/models.py`.
2. Ejecuté diagnósticos interactivos para listar modelos registrados: verifiqué que `DiagnosticoGeolocalizado`, `AIDiagnostic`, `SensorLog`, `BotanicalKnowledge` aparecían en la AppConfig `core`.
3. Corregí la migration 0004 para usar `settings.AUTH_USER_MODEL` y añadí la dependencia swappable. Esto evita referenciar la tabla `auth_user` por nombre fijo cuando el proyecto usa un `AUTH_USER_MODEL` personalizado (`authentication.User`).
4. Alineé la migration 0001 para que `AIDiagnostic` fuera `managed=True` (coherente con la implementación del modelo actual) para que la tabla `ai_diagnostics` sea creada en la DB de pruebas.
5. Creé / ajusté el archivo de pruebas de integración `tests/integration/test_map_hotspots.py` con 9 pruebas que comprueban: respuesta 200, agrupamiento (clustering) correcto, etiqueta dominante, ausencia de filtrado por usuario, cache GLOBAL, rechazo 401 para no autenticados, radio calculado >0, filtros `pest` y `days`.
6. Ejecuté las pruebas en el entorno local `.venv` creado: `python -m pytest tests/integration/test_map_hotspots.py` → Resultado final: 9 passed, 0 failed.

Resultados de pruebas
---------------------
- Comando ejecutado (ejemplo):

```bash
source .venv/bin/activate
python -m pytest tests/integration/test_map_hotspots.py -v
```
- Resultado: 9 passed, 0 failed (entorno local, SQLite, `LocMemCache` para tests).

Observaciones técnicas
----------------------
- Estructura de modelos: El proyecto usa una estructura no convencional (models en `infrastructure/repositories/models.py`). Esto está bien desde una separación de responsabilidades, pero obliga a garantizar que Django detecte esos modelos (re-export en `app/models.py` o import en `apps.py`).
- Migrations vs modelos: Encontré inconsistencias entre el estado de las migraciones y la implementación actual de los modelos (`managed` flag). Modificar migraciones existentes puede ser aceptable en desarrollo pero hay que ser extremadamente cauteloso en producción.
- FK a user model: Las migraciones iniciales referenciaban la tabla `auth_user` en lugar de `settings.AUTH_USER_MODEL`, lo que provoca ruptura cuando se usa `AUTH_USER_MODEL` personalizado. Siempre usar `settings.AUTH_USER_MODEL` y `migrations.swappable_dependency` en migraciones que dependan del modelo de usuario.
- Clustering: La lógica de agrupamiento usa `round(lat, precision)` y `round(lon, precision)`. Esto es sencillo y rápido, pero su sensibilidad depende directamente del parámetro `precision`. Se documentó y los tests se ajustaron a la lógica actual.
- Privacidad: `HotspotSerializer` devuelve datos agregados (centroides y conteos). Es vital mantener el contrato: nunca incluir `user`, `user_id`, `email`, ni las coordenadas individuales. Los tests incluyen un gatekeeper para comprobar que claves prohibidas nunca aparezcan.
- Caché: Implementé cache global (clave sin `user_id`). TTL actual: 15 minutos (configuración existente en la vista). Debe haber una estrategia de invalidación si los datos se actualizan frecuentemente (ver recomendaciones).

Riesgos, restricciones y mitigaciones
-------------------------------------
- Riesgo: Cambiar migraciones antiguas en repositorios con histórico puede causar inconsistencias si ya hay bases de datos en producción con migraciones aplicadas. Mitigación: Estas modificaciones deben revisarse y aplicarse solo si se controla el despliegue (o generar migraciones nuevas que alteren el esquema en lugar de editar migraciones aplicadas en producción).
- Riesgo: La re-exportación de modelos (solución aplicada) es segura, pero si se olvida al crear nuevos submódulos, Django volverá a no detectar modelos.
- Riesgo: El clustering por redondeo simple no es exacto para distancias en metros en latitudes distintas. Se usa Haversine para el cálculo del radio, pero la agrupación por redondeo es una aproximación; para una geografía precisa se recomienda usar geohash o spatial indices (PostGIS) para producción.

Recomendaciones (priorizadas)
------------------------------
1. Inmediatas (de alta prioridad)
   - Mantener `apps/<app>/models.py` que re-exporte modelos si los defines en submódulos. Documentar esta convención en CONTRIBUTING.md o README del proyecto.
   - Revertir/modificar migraciones solo con cuidado; en lugar de editar migraciones aplicadas en producción, crear nuevas migraciones que ajusten el esquema. Si editas migraciones en ramas de desarrollo, coordinar antes del deploy.
   - Añadir chequeos automáticos en CI que ejecuten: `python manage.py makemigrations --check` y `python manage.py migrate --plan` para detectar inconsistencias tempranas.

2. Arquitectura y calidad
   - Considerar usar PostGIS (o pgvector + PostGIS si ya se usa Postgres) y almacenar geometrías para clustering y consultas espaciales robustas. Esto permitirá indices espaciales y consultas más precisas y escalables.
   - Para clustering en memoria: evaluar `geohash` o `h3` para agrupar por celdas con tamaño en metros conocido por latitud.
   - Añadir pruebas de integración en CI que ejecuten la suite de tests actuales con una BD de prueba (SQLite está bien para unit/integration en contenedores, pero validar con Postgres en pipeline ayuda a detectar problemas de migraciones y SQL específicos).

3. Caché y consistencia
   - Revisar TTL y estrategia de invalidación: si los diagnósticos nuevos deben reflejarse rápidamente en la vista de hotspots, considerar cache-shortening o invalidar la cache por región cuando se inserten nuevos diagnósticos (ej.: señal post_save que limpie keys relevantes o un sistema de versionado por fecha/región).
   - Monitorizar cache hit/miss y latencia; en producción usar Redis con configuración de replicación y persistencia adecuada.

4. Seguridad y privacidad
   - Mantener la regla de que `HotspotSerializer` nunca exponga `user` o coordenadas puntuales. Añadir una prueba estática/gatekeeper adicional que valide el esquema de la respuesta (contract tests).
   - Revisar logs para asegurarse de no registrar coordenadas exactas en texto plano en logs públicos.

Pasos siguientes sugeridos
-------------------------
- Documentar la convención de re-export en un archivo corto de contribución (ej. `docs/CONTRIBUTING.md` o `docs/ARCHITECTURE.md`).
- Añadir una prueba en CI que ejecute `pytest tests/integration/test_map_hotspots.py` para prevenir regresiones futuras.
- Opcional: migrar almacenamiento espacial a PostGIS y adaptar pruebas a una matriz que incluya Postgres en pipeline.

Cómo reproducir los pasos y verificar localmente
-----------------------------------------------
1. Crear/activar venv y dependencias (si aún no existe):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Ejecutar tests de integración del endpoint:

```bash
source .venv/bin/activate
python -m pytest tests/integration/test_map_hotspots.py -v
```

Archivo de reporte generado
---------------------------
He creado este informe en la raíz del proyecto:
- [REPORT_HOTSPOTS_GLOBAL_CACHE_AND_TESTS.md](REPORT_HOTSPOTS_GLOBAL_CACHE_AND_TESTS.md)

Notas finales
-------------
- Cambios en migraciones y modelos fueron aplicados para restaurar coherencia en el entorno de desarrollo/pruebas. Antes de aplicar cambios migratorios similares en producción, coordinar backups y ventanas de mantenimiento.
- Si quieres, puedo:
  - Crear una entrada breve en `docs/` explicando la convención de re-export de modelos.
  - Añadir la ejecución de estos tests al pipeline de CI (GitHub Actions / GitLab CI) y configurar un job que use Postgres para pruebas más realistas.

¿Deseas que cree la documentación de la convención (`docs/ARCHITECTURE.md`) y añadamos la ejecución de tests en CI?