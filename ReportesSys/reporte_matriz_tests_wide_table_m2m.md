# Matriz de Pruebas Automatizadas - Wide Table + M2M

## Cobertura objetivo
Validar integridad y trazabilidad end-to-end tras migracion EAV -> Wide Table:
- Tipado estricto de `plant_id` (UUID).
- Persistencia de sensores planos (`air_temperature`, `soil_humidity`, `uv_index`, `light_level`, `ph_level`).
- Tolerancia a nulos (`ph_level` opcional).
- Ausencia de silencios de datos en agregacion y explicabilidad.
- Autenticacion M2M obligatoria (`X-Hardware-Api-Key`).

## Prioridad HIGH (bloqueante de release)
1. `tests/integration/test_m2m_ingest_wide_table.py::test_sensor_data_m2m_success_flat_payload_creates_single_row`
- Riesgo cubierto: perdida de campos/tipos en ingesta.
- Esperado: `201`, insercion plana con `plant_id` UUID y `recorded_at` del payload.

2. `tests/integration/test_m2m_ingest_wide_table.py::test_sensor_data_m2m_rejects_missing_api_key`
- Riesgo cubierto: bypass de seguridad M2M.
- Esperado: `401` cuando falta `X-Hardware-Api-Key`.

3. `ai_rag_service/tests/test_explain_ph_endpoint_contract.py::test_explain_ph_rejects_invalid_uuid_in_plant_id`
- Riesgo cubierto: drift de tipado en FastAPI.
- Esperado: `422` para UUID invalido.

4. `ai_rag_service/tests/test_explain_ph_use_case_wide_table.py::test_explain_use_case_accepts_wide_table_air_temperature_and_null_ph_level`
- Riesgo cubierto: silencio de alertas por mismatch `temperature` vs `air_temperature`.
- Esperado: alertas termicas presentes y ejecucion estable con `ph_level=None`.

## Prioridad MEDIUM (estabilidad operativa)
5. `tests/integration/test_m2m_ingest_wide_table.py::test_sensor_data_m2m_rejects_missing_plant_id`
- Esperado: `400` con detalle de validacion.

6. `tests/integration/test_m2m_ingest_wide_table.py::test_sensor_batch_m2m_bulk_insert_success`
- Esperado: `201`, `registered` consistente con lote.

7. `tests/test_ai_models/test_sensor_data_aggregator.py::test_aggregator_returns_empty_dict_when_no_rows`
- Esperado: `{}` si no hay telemetria en ventana.

8. `ai_rag_service/tests/test_explain_ph_use_case_wide_table.py::test_explain_use_case_handles_empty_sensor_dict_without_crash`
- Esperado: fallback seguro (`hardcoded_default`) sin excepcion.

## Prioridad LOW (regresion funcional)
9. `tests/integration/test_m2m_ingest_wide_table.py::test_sensor_data_m2m_accepts_null_ph_level`
- Esperado: `201`, null persistido sin error.

10. `tests/test_ai_models/test_sensor_data_aggregator.py::test_aggregator_returns_flat_wide_table_fields_only`
- Esperado: salida plana, omite columnas null (`ph_level`).

## Scripts listos para ejecutar
Desde la raiz del repo:

```bash
pytest tests/integration/test_m2m_ingest_wide_table.py -q
pytest tests/test_ai_models/test_sensor_data_aggregator.py -q
pytest ai_rag_service/tests/test_explain_ph_use_case_wide_table.py -q
pytest ai_rag_service/tests/test_explain_ph_endpoint_contract.py -q
```

Suite completa:

```bash
pytest tests ai_rag_service/tests -q
```

## Dependencias de test requeridas
Si no estan instaladas:

```bash
pip install pytest pytest-django
```

## Criterio de aprobacion
- 100% de casos HIGH en verde.
- 0 fallos de autenticacion M2M.
- 0 fallos de contrato UUID en endpoint `/api/v1/explain/ph`.
- 0 excepciones con `sensors={}` o `ph_level=None`.
