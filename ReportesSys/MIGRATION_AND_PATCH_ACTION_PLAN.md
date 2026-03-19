# Migration Squash & PATCH Endpoint — Action Plan

> **Documento complementario de:** `DJANGO_BACKEND_REQUIREMENTS_AND_DEBT.md`  
> **Objetivo:** Checklist técnica paso a paso con comandos exactos de terminal  
> **Alcance:** Resolución de DT-01 (Schema Drift / Squash), DT-02 (Endpoint PATCH faltante), DT-04 (Throttle no aplicado)  
> **Fecha:** 16 de marzo de 2026

---

## Tabla de Contenidos

1. [Fase 0 — Diagnóstico del estado actual](#fase-0--diagnóstico-del-estado-actual)
2. [Fase 1 — Squash de migraciones a canónica inicial](#fase-1--squash-de-migraciones-a-canónica-inicial)
3. [Fase 2 — Implementar PATCH /api/v1/sensor-data/\<id\>/](#fase-2--implementar-patch-apiv1sensor-dataid)
4. [Fase 3 — Aplicar throttle a endpoints IoT](#fase-3--aplicar-throttle-a-endpoints-iot)
5. [Fase 4 — Migración a PostgreSQL para desarrollo local](#fase-4--migración-a-postgresql-para-desarrollo-local)
6. [Fase 5 — Validación CI y checklist de producción](#fase-5--validación-ci-y-checklist-de-producción)

---

## Fase 0 — Diagnóstico del estado actual

### 0.1 Verificar migraciones aplicadas

```bash
# Desde la raíz del proyecto
python manage.py showmigrations core
python manage.py showmigrations authentication
python manage.py showmigrations plants
```

**Output esperado:** Cada migración con `[X]` (aplicada) o `[ ]` (pendiente).  
**Acción:** Si alguna migración está pendiente, **NO CONTINUAR** sin antes documentar cuáles faltan.

### 0.2 Inspeccionar esquema real de la tabla `sensor_logs`

```bash
# SQLite (local)
python manage.py dbshell <<< ".schema sensor_logs"

# PostgreSQL (staging/prod)
python manage.py dbshell <<< "\d sensor_logs"
```

**Columnas esperadas (estado final post-0007):**

| Columna | Tipo | Nullable |
|---------|------|----------|
| `id` | bigint (autoincrement) | NO |
| `plant_id` | uuid | NO |
| `recorded_at` | datetime | NO |
| `soil_humidity` | float | SÍ |
| `air_humidity` | float | SÍ |
| `air_temperature` | float | SÍ |
| `uv_index` | float | SÍ |
| `light_level` | float | SÍ |
| `ph_level` | float | SÍ |

**Si existen columnas antiguas (`device_id`, `sensor_type`, `value`, `unit`, `user_id`, `timestamp`, `location_*`):** la migración `0007` no fue aplicada correctamente. Aplicar manualmente o continuar al squash.

### 0.3 Verificar que no hay migraciones pendientes sin generar

```bash
python manage.py makemigrations --check --dry-run
```

**Output esperado:** `No changes detected`  
**Si detecta cambios:** los modelos y migraciones están desincronizados. Generar y revisar antes de continuar.

### 0.4 (Solo prod) Volcar esquema actual

```bash
# PostgreSQL — solo esquema, sin datos
pg_dump --schema-only \
  --dbname="$DATABASE_URL" \
  --file=ReportesSys/schema_snapshot_$(date +%Y%m%d).sql
```

---

## Fase 1 — Squash de migraciones a canónica inicial

### 1.1 Crear rama de trabajo

```bash
git checkout -b fix/migration-squash-canonical
```

### 1.2 Squash de migraciones `core`

```bash
python manage.py squashmigrations core 0001 0007 --squashed-name canonical_initial
```

> **Nota:** Django generará una nueva migración con el flag `replaces = [('core', '0001_initial'), ..., ('core', '0007_...')]`. Revisarla manualmente.

### 1.3 Revisar la migración squashed

Abrir `apps/core/migrations/0001_canonical_initial.py` y verificar:

- [ ] `managed = True` en `SensorLog` (NO `False`)
- [ ] `SensorLog` solo tiene columnas wide-table (NO columnas EAV antiguas)
- [ ] `AIDiagnostic` tiene UUID PK y campos mínimos (NO campos legacy como `condition_name`, `severity`, `diagnostic_type`)
- [ ] `BotanicalKnowledge` incluye `VectorField(dimensions=1536)`
- [ ] `FeedbackTicket.user` y `DiagnosticoGeolocalizado.user` usan `on_delete=SET_NULL`
- [ ] NO quedan referencias a modelos eliminados (`PlantKnowledge`)

### 1.4 Limpiar artefactos contradictorios

```bash
# Crear directorio de archivo
mkdir -p apps/core/migrations/_archive

# Mover migraciones originales (preservar para historial)
for f in 0001_initial 0002_alter 0003_wide_table 0004_diagnosticos 0005_botanical 0006_sensorlog_hardware 0007_remove; do
  mv apps/core/migrations/${f}*.py apps/core/migrations/_archive/ 2>/dev/null
done
```

> **⚠️ IMPORTANTE:** Solo mover después de que la squashed esté verificada y tenga `replaces = [...]`.

### 1.5 Aplicar en staging con `--fake-initial`

```bash
# En staging (tablas ya existen)
python manage.py migrate core --fake-initial

# Verificar
python manage.py showmigrations core
```

### 1.6 Squash de migraciones `authentication` y `plants` (si necesario)

```bash
# Solo si tienen más de 2 migraciones
python manage.py showmigrations authentication
python manage.py showmigrations plants

# Si se necesita squash
python manage.py squashmigrations authentication 0001 0002 --squashed-name canonical_initial
python manage.py squashmigrations plants 0001 0001 --squashed-name canonical_initial
```

### 1.7 Test completo tras squash

```bash
# Borrar DB local para probar desde cero
rm -f db.sqlite3
python manage.py migrate
python manage.py makemigrations --check --dry-run

# Ejecutar suite de tests
python -m pytest tests/ -v --tb=short
```

---

## Fase 2 — Implementar PATCH /api/v1/sensor-data/\<id\>/

### 2.1 Crear serializer de actualización parcial

**Archivo:** `apps/core/presentation/serializers.py`

Añadir al final del archivo:

```python
class SensorDataPatchSerializer(serializers.Serializer):
    """
    Serializer para actualización parcial de SensorLog
    desde el microservicio de IA (Two-Stream Merge).
    Solo permite actualizar campos inferidos por CNN.
    """
    ph_level = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=14.0,
        allow_null=True,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided for update."
            )
        return attrs
```

### 2.2 Crear vista PATCH

**Archivo:** `apps/core/presentation/views.py`

Añadir la vista:

```python
from apps.core.presentation.serializers import SensorDataPatchSerializer

@api_view(['PATCH'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
@throttle_classes([SensorDataThrottle])
def sensor_data_patch_view(request, pk):
    """
    PATCH /api/v1/sensor-data/<id>/
    Two-Stream Merge: permite al microservicio IA actualizar
    ph_level (inferido por CNN) en un SensorLog existente.
    Auth: X-Hardware-Api-Key (M2M server-to-server).
    """
    try:
        sensor_log = SensorLog.objects.get(pk=pk)
    except SensorLog.DoesNotExist:
        return Response(
            {"error": "SensorLog not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = SensorDataPatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    updated_fields = []
    for field, value in serializer.validated_data.items():
        setattr(sensor_log, field, value)
        updated_fields.append(field)

    sensor_log.save(update_fields=updated_fields)

    return Response(
        {
            "status": "updated",
            "sensor_log_id": sensor_log.pk,
            "updated_fields": updated_fields,
        },
        status=status.HTTP_200_OK,
    )
```

### 2.3 Registrar URL

**Archivo:** `apps/core/presentation/urls.py`

Añadir **antes** de `sensor-data/` (para evitar colisión):

```python
from apps.core.presentation.views import sensor_data_patch_view

# Dentro de urlpatterns, ANTES de path('sensor-data/', ...)
path('sensor-data/<int:pk>/', sensor_data_patch_view, name='sensor-data-patch'),
```

**urlpatterns completo recomendado (sección IoT):**

```python
urlpatterns = [
    # IoT endpoints — orden importa para evitar shadowing
    path('sensor-data/batch/', sensor_batch_view, name='sensor-data-batch'),
    path('sensor-data/latest/', mock_sensor_data, name='sensor-data-latest'),
    path('sensor-data/<int:pk>/', sensor_data_patch_view, name='sensor-data-patch'),  # NUEVO
    path('sensor-data/', sensor_data_view, name='sensor-data'),
    # ... resto de URLs
]
```

### 2.4 Imports necesarios en views.py

Verificar que estos imports existan:

```python
from apps.core.infrastructure.repositories.models import SensorLog
from apps.core.presentation.serializers import SensorDataPatchSerializer
from apps.core.presentation.throttles import SensorDataThrottle
from apps.authentication.infrastructure.authentication import HardwareAPIKeyAuthentication
# HardwareOnlyPermission ya debe estar importado para las vistas IoT existentes
```

### 2.5 Test unitario para el endpoint PATCH

**Archivo:** `tests/test_core_views/test_sensor_data_patch.py`

```python
"""
Tests para PATCH /api/v1/sensor-data/<id>/ (Two-Stream Merge).
"""
import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from apps.core.infrastructure.repositories.models import SensorLog
from apps.plants.infrastructure.repositories.models import UserPlant
import uuid


HARDWARE_API_KEY = "test-hardware-key-for-ci"


@pytest.fixture
def hw_client():
    client = APIClient()
    client.credentials(HTTP_X_HARDWARE_API_KEY=HARDWARE_API_KEY)
    return client


@pytest.fixture
def sensor_log(db):
    plant_id = uuid.uuid4()
    return SensorLog.objects.create(
        plant_id=plant_id,
        soil_humidity=45.0,
        air_temperature=22.0,
        ph_level=None,
    )


@override_settings(HARDWARE_API_KEY=HARDWARE_API_KEY)
class TestSensorDataPatch:
    """Two-Stream Merge endpoint tests."""

    def test_patch_ph_level_success(self, hw_client, sensor_log):
        """AI microservice can inject pH after CNN inference."""
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        response = hw_client.patch(url, {"ph_level": 6.3}, format="json")

        assert response.status_code == 200
        assert response.data["status"] == "updated"
        assert response.data["sensor_log_id"] == sensor_log.pk

        sensor_log.refresh_from_db()
        assert sensor_log.ph_level == pytest.approx(6.3)

    def test_patch_ph_out_of_range(self, hw_client, sensor_log):
        """pH must be in [0.0, 14.0]."""
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        response = hw_client.patch(url, {"ph_level": 15.0}, format="json")
        assert response.status_code == 400

    def test_patch_empty_body_rejected(self, hw_client, sensor_log):
        """Empty body must be rejected."""
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        response = hw_client.patch(url, {}, format="json")
        assert response.status_code == 400

    def test_patch_nonexistent_log(self, hw_client, db):
        """404 for non-existent SensorLog."""
        response = hw_client.patch(
            "/api/v1/sensor-data/999999/",
            {"ph_level": 7.0},
            format="json",
        )
        assert response.status_code == 404

    def test_patch_without_api_key_rejected(self, sensor_log):
        """Unauthenticated request rejected."""
        client = APIClient()
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        response = client.patch(url, {"ph_level": 6.0}, format="json")
        assert response.status_code in (401, 403)

    def test_patch_idempotent(self, hw_client, sensor_log):
        """Patching same value twice produces same result."""
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        hw_client.patch(url, {"ph_level": 6.3}, format="json")
        response = hw_client.patch(url, {"ph_level": 6.5}, format="json")

        assert response.status_code == 200
        sensor_log.refresh_from_db()
        assert sensor_log.ph_level == pytest.approx(6.5)
```

### 2.6 Comandos para ejecutar los tests

```bash
# Ejecutar solo los tests del PATCH endpoint
python -m pytest tests/test_core_views/test_sensor_data_patch.py -v

# Ejecutar toda la suite para verificar que no se rompe nada
python -m pytest tests/ -v --tb=short
```

---

## Fase 3 — Aplicar throttle a endpoints IoT

### 3.1 Problema

`SensorDataThrottle` está definido en `apps/core/presentation/throttles.py` pero **no se aplica** en las vistas `sensor_data_view` ni `sensor_batch_view`.

### 3.2 Fix

**Archivo:** `apps/core/presentation/views.py`

Añadir decorador `@throttle_classes` a las vistas IoT:

```python
from apps.core.presentation.throttles import SensorDataThrottle

@api_view(['POST'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
@throttle_classes([SensorDataThrottle])          # ← AÑADIR
def sensor_data_view(request):
    # ... código existente sin cambios ...

@api_view(['POST'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
@throttle_classes([SensorDataThrottle])          # ← AÑADIR
def sensor_batch_view(request):
    # ... código existente sin cambios ...
```

### 3.3 Verificar en settings.py

```python
# mole_ai_backend/settings.py → REST_FRAMEWORK
'DEFAULT_THROTTLE_RATES': {
    'anon': '100/hour',
    'user': '1000/hour',
    'llm_chat': '60/minute',
    'diagnostics': '30/minute',
    'sensor_data': '200/minute',  # ← Debe existir
}
```

---

## Fase 4 — Migración a PostgreSQL para desarrollo local

### 4.1 docker-compose.yml — Servicio PostgreSQL local

Agregar o verificar que exista en `docker-compose.yml`:

```yaml
services:
  postgres-dev:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: mole_ai_dev
      POSTGRES_USER: mole_dev
      POSTGRES_PASSWORD: ${POSTGRES_DEV_PASSWORD:-dev_only_change_me}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

> **Nota:** `pgvector/pgvector:pg16` incluye la extensión pgvector preinstalada.

### 4.2 settings.py — Base de datos unificada

Reemplazar la condición `DEBUG → SQLite / else → Postgres` por:

```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://mole_dev:dev_only_change_me@localhost:5432/mole_ai_dev',
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=not DEBUG,
    )
}
```

### 4.3 Crear extensión pgvector

```bash
docker compose up -d postgres-dev
python manage.py dbshell <<< "CREATE EXTENSION IF NOT EXISTS vector;"
python manage.py migrate
```

### 4.4 Verificar VectorField funciona

```bash
python manage.py shell -c "
from apps.core.infrastructure.repositories.models import BotanicalKnowledge
print(BotanicalKnowledge._meta.get_field('embedding').db_type(None))
"
# Esperado: 'vector(1536)'
```

---

## Fase 5 — Validación CI y checklist de producción

### 5.1 Guard de migraciones en CI

Añadir a `.github/workflows/ci.yml` (o equivalente):

```yaml
- name: Check for missing migrations
  run: python manage.py makemigrations --check --dry-run
```

### 5.2 Checklist pre-producción

- [ ] `python manage.py showmigrations` — todas `[X]`
- [ ] `python manage.py makemigrations --check` — `No changes detected`
- [ ] `pg_dump --schema-only` coincide con ERD del documento de auditoría
- [ ] Endpoint `PATCH /api/v1/sensor-data/<id>/` responde `200` con API Key válida
- [ ] Endpoint `PATCH` rechaza requests sin API Key (`401/403`)
- [ ] `SensorDataThrottle` activo en `sensor_data_view`, `sensor_batch_view`, `sensor_data_patch_view`
- [ ] `BotanicalKnowledge.embedding` es `vector(1536)` en `\d botanical_knowledge`
- [ ] Migraciones archivadas en `_archive/` no interfieren (directorio excluido de Django via `__init__.py` ausente o directorio sin `.py`)
- [ ] Tests pasan: `python -m pytest tests/ -v --tb=short`
- [ ] `.env` de producción con `HARDWARE_API_KEY` rotado (no el de dev)

### 5.3 Rollback plan

```bash
# Si el squash causa problemas en staging:
git checkout main -- apps/core/migrations/
python manage.py migrate core --fake

# Si el PATCH endpoint presenta conflictos:
git revert HEAD  # asumiendo commit aislado
```

---

## Resumen de Archivos a Modificar

| Archivo | Cambio | Fase |
|---------|--------|------|
| `apps/core/migrations/` | Squash → `0001_canonical_initial.py` | 1 |
| `apps/core/presentation/serializers.py` | Añadir `SensorDataPatchSerializer` | 2 |
| `apps/core/presentation/views.py` | Añadir `sensor_data_patch_view`, decorar IoT con throttle | 2, 3 |
| `apps/core/presentation/urls.py` | Registrar `sensor-data/<int:pk>/` | 2 |
| `tests/test_core_views/test_sensor_data_patch.py` | Crear suite de tests PATCH | 2 |
| `docker-compose.yml` | Servicio PostgreSQL local | 4 |
| `mole_ai_backend/settings.py` | `dj_database_url` unificado | 4 |
| `.github/workflows/ci.yml` | Guard de migraciones | 5 |

---

> **Siguiente paso:** Ejecutar Fase 0 para diagnosticar el estado actual del esquema antes de proceder con el squash.
