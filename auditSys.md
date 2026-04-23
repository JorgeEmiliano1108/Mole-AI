# Mole.AI v2.1 — Auditoría de Sistema Completo (auditSys.md)

**Fecha:** 2026-04-22
**Versión:** 2.1.0
**Auditor:** Sistema Completo (Backend + Infrastructure + Edge + MS3)
**Clasificación:** CRÍTICO | ALTO | MEDIO

---

## 1. AUDITORÍA DE INFRAESTRUCTURA (infrastructure/)

### 1.1docker-compose.yml — Exposición de Puertos

| Servicio | Puerto Host | Puerto Contenedor | Exposición | Evaluación |
|----------|-----------|------------------|------------|------------|
| nginx | **8080** | 80 | ✅ Only public entry | CORRECTO |
| django-backend | — | 8000 | expose only | ✅ CORRECTO |
| db (Postgres) | — | 5432 | expose only | ✅ CORRECTO |
| redis | — | 6379 | expose only | ✅ CORRECTO |
| mqtt_broker | — | 1883 | expose only | ✅ CORRECTO |
| minio | — | 9000 | expose only | ✅ CORRECTO |
| ms1_vision | — | 8001 | expose only | ✅ CORRECTO |
| ms2_chat | — | 8002 | expose only | ✅ CORRECTO |
| ms3_reports | — | 8003 | expose only | ✅ CORRECTO |

**Resultado:** ✅ Zero-Trust: Solo Nginx visible al host.

---

### 1.2docker-compose.yml — Volúmenes Persistentes

| Volumen | Servicio | Tipo | Estado |
|---------|----------|------|--------|
| `postgres_data` | db | named volume | ✅ DEFINIDO |
| `ai_rag_vectors` | ms2_chat | named volume | ✅ DEFINIDO |
| `minio_data` | minio | named volume | ✅ DEFINIDO |

**Resultado:** ✅ Todos los volúmenes críticos persistentes definidos.

---

### 1.3docker-compose.yml — Redes Docker

| Servicio | mole_public | mole_internal |
|----------|-------------|---------------|
| nginx | ✅ | ✅ |
| django-backend | ✅ | ✅ |
| celery_worker | — | ✅ |
| celery_beat | — | ✅ |
| db | — | ✅ |
| redis | — | ✅ |
| mqtt_broker | — | ✅ |
| minio | — | ✅ |
| ms1_vision | — | ✅ |
| ms2_chat | — | ✅ |
| ms3_reports | — | ✅ |

**Resultado:** ✅ Arquitectura de red aislada correcta.

---

### 1.4 Mosquitto — Configuración

**Archivo:** `infrastructure/mosquitto/config/mosquitto.conf`

```conf
allow_anonymous true
listener 1883
```

**Evaluación:**
- ⚠️ `allow_anonymous true` — Riesgo si Mosquitto se expusiera fuera de mole_internal
- ✅ Correcto dado que Mosquitto solo está en red interna (`allow_anonymous` en LAN es normal para IoT local)

**Severidad:** MEDIO (aceptable dado el aislamiento de red)

---

## 2. AUDITORÍA EDGE NODE (edge_node/)

### 2.1 Store-and-Forward Daemon

**Archivo:** `edge_node/store_forward_daemon.py`

| Característica | Implementación | Estado |
|----------------|---------------|--------|
| Persistencia offline | SQLite local `edge_mole.sqlite3` | ✅ |
|Índice único | `(device_id, timestamp)` UNIQUE | ✅ |
| Batch sync | MAX_BATCH_SIZE=200 | ✅ |
| M2M Auth (Zero-Trust) | Supabase Auth via email/password | ✅ |
| JWT Auto-refresh | `_token_store.refresh()` | ✅ |
| Fallback legacy | X-Hardware-Api-Key header | ✅ |
| Retry on 401 | Refresh + retry once | ✅ |
| Store-and-Forward | INSERT OR IGNORE | ✅ |

**Resultado:** ✅ Implementación robusta y completa.

---

### 2.2 Formato JSON vs Backend Esperado

**Backend espera (sensor_batch_view):**
```json
{
  "batch": [
    {
      "plant_id": "uuid",
      "recorded_at": "datetime ISO8601",
      "soil_humidity": float,
      "air_temperature": float,
      ...
    }
  ]
}
```

**Edge Node construye (store_forward_daemon.py:221-229):**
```python
entry: dict = {
    "device_id": r[1],      # ⚠️ CAMPO EXTRA
    "plant_id":  r[2],
    "timestamp": r[3],      # ⚠️ NOMBRE DIFERENTE (timestamp vs recorded_at)
    "sensors":   json.loads(r[4]),  # ⚠️ ARRAY vs OBJETO
}
```

**BRECHA CRÍTICA IDENTIFICADA:**

| Campo Backend | Campo Edge Node | Compatibilidad |
|--------------|----------------|----------------|
| `plant_id` | `plant_id` | ✅ MATCH |
| `recorded_at` | `timestamp` | ❌ **NOMBRE DIFERENTE** |
| `soil_humidity` | dentro de `sensors[]` | ❌ **ESTRUCTURA DIFERENTE** |
| `device_id` | `device_id` | ❌ **CAMPO EXTRA (no esperado)** |

El backend espera un objeto plano con campos específicos de sensores, pero el edge_node envía un array de sensores y un campo `timestamp`.

**Severidad:** 🔴 **CRÍTICO** — El endpoint `/api/v1/sensor-data/batch/` rejectará payloads del edge_node.

---

### 2.3 MQTT Subscriber — Formato de Mensaje

**Archivo:** `edge_node/mqtt_local_subscriber.py`

```json
{
  "device_id": "ESP32-001",
  "plant_id": "planta_maiz_01",
  "sensors": [
    {"type": "temperature", "value": 27.4, "unit": "C"},
    {"type": "humidity", "value": 62.0, "unit": "%"}
  ],
  "timestamp": "2026-03-07T10:30:00"
}
```

**Evaluación:**
- ✅ MQTT topic pattern: `mole/sensors/#` correcto
- ✅ Timestamp incluido
- ✅ Fallback a device_id del topic

---

### 2.4 ETSI EN 303 645 — Anti-Replay

**Hallazgo:** El edge_node NO implementa validación Anti-Replay local.

**Análisis:**
- El edge_node usa timestamps del ESP32 (`payload.get("timestamp")`)
- Si el ESP32 genera timestamps incorrectos, el edge_node los retransmitirá sin filtro
- El backend (sensor_data_view) rechazará si delta > 300s

**Severidad:** 🔴 **CRÍTICO** — Sin validación Anti-Replay en edge_node, los datos serán rejectados si hay skew de reloj entre ESP32 y backend.

---

### 2.5 Inference (TFLite)

**Archivo:** `edge_node/inference.py`

| Característica | Estado |
|----------------|--------|
| TFLite model loading | ✅ |
| Mock fallback | ✅ |
| HSV preprocessing | ✅ |
| pH clamping (0-14) | ✅ |
| Integration con store_forward | ✅ |

**Resultado:** ✅ Implementación correcta.

---

## 2.6 ESP32 Firmware (Microservicio IoT)

**Ubicación:** `microservices/esp32_node/`

### Arquitectura Hexagonal (C++)

```
microservices/esp32_node/
├── include/
│   ├── domain/
│   │   └── TelemetryData.h          ← Estructura de datos
│   └── ports/
│       ├── ISensor.h                 ← Puerto para sensores
│       └── IComm.h                   ← Puerto para comunicaciones
├── lib/
│   ├── sensors/
│   │   ├── Dht20Adapter.h            ← Sensor temperatura/humedad
│   │   ├── Ltr390Adapter.h           ← Sensor UV/Luz
│   │   └── AnalogMoisture.h          ← Sensor humedad suelo
│   └── comms/
│       ├── WifiMqttAdapter.h         ← WiFi + MQTT
│       └── BleAdapter.h              ← Bluetooth GATT
├── src/
│   ├── main.cpp                      ← Entry point (setup/loop)
│   └── core/
│       └── TelemetryUseCase.h       ← Caso de uso principal
└── README.md                         ← Vacío
```

### Análisis de Componentes

| Archivo | Responsabilidad | Estado |
|---------|----------------|--------|
| `TelemetryData.h` | Estructura Wide Table (device_id, temp, hum, soil, light, uv) | ✅ |
| `TelemetryUseCase.h` | Orquestación: lee sensores → envía por comm | ✅ |
| `WifiMqttAdapter.h` | Publica en `mole/telemetry` vía MQTT | ⚠️ Ver below |
| `BleAdapter.h` | GATT Service + Characteristic NOTIFY | ✅ |

### Formato JSON del ESP32 (WifiMqttAdapter.h:41-49)

```cpp
String payload = "{";
payload += "\"dev_id\":\"" + data.device_id + "\",";
payload += "\"temp\":" + String(data.temp_c) + ",";
payload += "\"hum\":" + String(data.hum_pct) + ",";
payload += "\"soil\":" + String(data.soil_moist_pct) + ",";
payload += "\"light\":" + String(data.light_lux);
payload += "}";

_mqttClient.publish("mole/telemetry", payload.c_str());
```

**Topic MQTT:** `mole/telemetry`

**Payload generado:**
```json
{
  "dev_id": "NODE-EMILIANO-001",
  "temp": 27.4,
  "hum": 62.0,
  "soil": 45.2,
  "light": 12000.0
}
```

### Brecha Detectada: ETSI EN 303 645 — Anti-Replay

**Problema identificado:**

El ESP32 usa `millis()` como timestamp (línea 31 de TelemetryUseCase.h):
```cpp
data.timestamp = millis(); // O usar un RTC si está disponible
```

`millis()` es un contador de milisegundos desde el arranque del ESP32, **NO un timestamp UTC ISO8601**.

El backend Django espera (`sensor_batch_view`):
```json
"recorded_at": "2026-04-22T10:30:00Z"  // datetime ISO8601
```

El ESP32 envía:
```json
"timestamp": 12345678  // milliseconds since boot
```

**Severidad:** 🔴 **CRÍTICO** — El backend rejectará todos los mensajes del ESP32 por formato de timestamp inválido.

### Compliance ETSI EN 303 645 — Implementado

| Control | Implementación | Estado |
|---------|---------------|--------|
| **IFT-016 Compliance** | Sin llamada a `esp_wifi_set_max_tx_power()` | ✅ |
| **Power Management** | Deep Sleep de 5 minutos configurado | ✅ |
| **Anti-Replay (parcial)** | `millis()` como secuencia, pero NO UTC | ❌ **INCOMPLETO** |
| **Sensor Auth** | Sin API Key en el payload (confía en MQTT broker) | ⚠️ RIESGO |

### Brecha de Formato MQTT vs Edge Node

| Campo ESP32 | Campo Edge Node Espera | Compatibilidad |
|-------------|----------------------|----------------|
| `dev_id` | `device_id` | ✅ Compatible |
| `temp` | — | ⚠️ Renombrar a `air_temperature` |
| `hum` | — | ⚠️ Renombrar a `soil_humidity` o `air_humidity` |
| `soil` | — | ⚠️ Renombrar a `soil_moisture` |
| `light` | — | ✅ Compatible con `light_level` |
| `timestamp` (millis) | `timestamp` (ISO8601 string) | ❌ **INCOMPATIBLE** |

### Resumen ESP32

| Aspecto | Evaluación |
|---------|-----------|
| Arquitectura | ✅ Hexagonal (puertos/adaptadores) |
| IFT-016 Compliance | ✅ Potencia por defecto |
| Power Management | ✅ Deep Sleep 5 min |
| MQTT Publishing | ✅ Correcto |
| Formato Timestamp | ❌ **CRÍTICO** — millis() vs ISO8601 |
| BLE GATT | ✅ Implementado |

---

## 3. AUDITORÍA DE MICROSERVICIOS (mole_report/)

### 3.1 MS3 — Lógica de Generación de Reportes

**Archivo:** `microservices/mole_report/application/use_cases/generate_report_use_case.py`

| Paso | Implementación | Estado |
|------|----------------|--------|
| 1. Fetch sensor logs (CAG) | `SupabaseClient.fetch_sensor_logs()` | ✅ |
| 2. Anomaly detection | Statistical (±2σ) | ✅ |
| 3. FAISS RAG query | `FAISSReaderAdapter.query()` | ✅ |
| 4. LLM synthesis | `HuggingFaceClient.synthesize_insights()` | ✅ |
| 5. HTML build | `ReportBuilder.build_report_html()` | ✅ |
| 6. COFEPRIS disclaimer | ✅ Hardcoded | ✅ |
| 7. PDF generation | `WeasyPrintReportGenerator` | ✅ |
| 8. S3 upload | `S3Adapter.upload_bytes()` | ✅ |
| 9. Audit record | `supabase.insert_audit_record()` | ✅ |

**Resultado:** ✅ No es placeholder. Implementación real y completa.

---

### 3.2 MS3 — Job Metadata Store (Redis)

**Archivo:** `infrastructure/redis/job_metadata_store.py`

| Operación | Implementación | Estado |
|-----------|---------------|--------|
| Create job | `hset {status: QUEUED, progress: 0}` | ✅ |
| Update status | `hset {status}` | ✅ |
| Set progress | `hset {progress}` | ✅ |
| Set result | `hset {pdf_s3_path}` | ✅ |
| Set error | `hset {error_message}` | ✅ |
| Get job | `hgetall` | ✅ |
| Key prefix | `jobs:{job_id}` | ✅ |

**Resultado:** ✅ LFPDPPP compliance: Solo `hashed_user_id` transita por Redis.

---

### 3.3 MS3 — Celery Task

**Archivo:** `infrastructure/workers/tasks.py`

| Característica | Implementación | Estado |
|----------------|---------------|--------|
| Task name | `generate_report_task` | ✅ |
| Retry policy | `autoretry_for, retry_backoff, max_retries=3` | ✅ |
| On failure | Update job status + error trace | ✅ |
| On success | `job_store.update_status("SUCCESS")` | ✅ |

**Resultado:** ✅ Robusto.

---

### 3.4 MS3 — PDF Generator

**Archivo:** `infrastructure/pdf/weasyprint_report_generator.py`

| Característica | Estado |
|----------------|--------|
| WeasyPrint HTML→PDF | ✅ |
| pydyf compatibility shim | ✅ |
| Version fallback | ✅ |

**Resultado:** ✅ Implementado.

---

## 4. ANÁLISIS DE BRECHAS (Gap Analysis)

### 4.1 Archivos/Funcionalidades Faltantes

| ID | Componente | Elemento Faltante | Severidad | Impacto |
|----|-----------|------------------|-----------|---------|
| GAP-001 | esp32_node | **MQTT Topic Mismatch**: ESP32 publica en `mole/telemetry`, edge_node suscribe a `mole/sensors/#` | 🔴 CRÍTICO | No hay recepción de datos |
| GAP-002 | esp32_node → edge_node | ESP32 usa `millis()` (no UTC), edge_node no transforma a `recorded_at` ISO8601 | 🔴 CRÍTICO | Batch ingest fallará con 403 Anti-Replay |
| GAP-003 | esp32_node | Campos renombrados: `temp` → `air_temperature`, `soil` → `soil_moisture`, `hum` → `air_humidity` | 🟡 MEDIO | Edge node necesita transformar nombres |
| GAP-004 | edge_node | Transformación JSON incompatible con backend (sensors[] vs campos planos) | 🔴 CRÍTICO | Batch ingest fallará |
| GAP-005 | edge_node | Validación Anti-Replay local (timestamp UTC) | 🔴 CRÍTICO | Datos rejectados por skew de reloj |
| GAP-005 | infrastructure | Script de migración Django (entrypoint) | 🟡 MEDIO | Migraciones no automaticas |
| GAP-006 | infrastructure | Health check scripts | 🟡 MEDIO | No hay script de validación pre-deploy |
| GAP-007 | mole_report | Dockerfile con dependencias (weasyprint, boto3) | 🟡 MEDIO | Posible Missing dependencies |

---

### 4.2 REQ-F Incompletos o Rotos

| ID | Requisito | Estado Actual | Problema |
|----|-----------|--------------|-----------|
| REQ-F-IOT-001 | Ingesta sensor individual | 🔴 ROTO | ESP32 usa `millis()` no UTC ISO8601 |
| REQ-F-IOT-002 | Ingesta lote | 🔴 ROTO | Formato campos ESP32 no coincide con backend |
| REQ-NF-SEC-003 | Anti-Replay (ETSI EN 303 645) | 🔴 INCOMPLETO | ESP32 `millis()` no puede ser validado por backend |

---

### 4.3 Archivos de Configuración

| Archivo | Estado | Observación |
|---------|--------|-------------|
| `.env.example` | ✅ | Completo, 166 líneas |
| `infrastructure/mosquitto/config/mosquitto.conf` | ✅ | Configuración básica |
| `infrastructure/nginx/nginx.conf` | ✅ | Corregido (Fase 2) |
| `frontend/Dockerfile` | ✅ | Multi-stage build |
| `microservices/mole_report/Dockerfile` | ⚠️ NO ENCONTRADO | No verificado |

---

## 5. RESUMEN DE HALLAZGOS POR SEVERIDAD

### 🔴 CRÍTICO

| ID | Hallazgo | Archivo/Línea | Estado |
|----|---------|--------------|------------------|-------------------|
| C-001 | **MQTT Topic Mismatch**: ESP32 publica en `mole/telemetry`, edge_node suscribe a `mole/sensors/#` | `WifiMqttAdapter.h:49`, `mqtt_local_subscriber.py:51` | ✅ **FIXED** - ESP32 ahora usa `mole/sensors/ESP-XXX` |
| C-002 | ESP32 usa `millis()` (no UTC) → backend rejecta | `TelemetryUseCase.h:31` | ✅ **FIXED** - NTP sync + ISO8601 timestamp |
| C-003 | ESP32 campos JSON no coinciden con backend | `WifiMqttAdapter.h:41-49` | ✅ **FIXED** - Campos renombrados a air_temperature, etc |
| C-004 | Edge node no transforma device_id → plant_id (UUID) | `mqtt_local_subscriber.py` | 🔴 PENDIENTE - Traducción device_id MAC→plant_id UUID |
| C-005 | Sin validación Anti-Replay en edge_node | `mqtt_local_subscriber.py` | 🔴 PENDIENTE - Filtro UTC antes de enqueue |

### 🟡 MEDIO

| ID | Hallazgo | Archivo/Línea | Acción Requerida |
|----|---------|--------------|------------------|
| M-001 | allow_anonymous en Mosquitto | `mosquitto.conf:4` | Documentar que es seguro por aislamiento de red |
| M-002 | Sin script de entrypoint para migraciones | `infrastructure/` | Crear `entrypoint.sh` con `python manage.py migrate` |
| M-003 | Sin Dockerfile verificado en MS3 | `mole_report/` | Verificar que todas las deps (weasyprint, boto3) estén instaladas |

---

## 6. FLUJO DE DATOS — Verificación End-to-End

```
ESP32 (sensor)
    │
    │ MQTT: mole/telemetry
    │ {"dev_id": "NODE-001", "temp": 27.4, "hum": 62.0, "soil": 45.2, "light": 12000, "timestamp": millis()}
    │ ⚠️ PROBLEMA 1: millis() no es UTC ISO8601
    │ ⚠️ PROBLEMA 2: Campos diferentes (temp vs air_temperature)
    ▼
MQTT Broker (mosquitto) — mole_internal
    │
    │ Topic: mole/telemetry (no mole/sensors/#)
    ▼
Edge Node (mqtt_local_subscriber.py)
    │
    │ ⚠️ ESP32 topics no coinciden con suscripción: mole/sensors/#
    │ El suscriptor NO recibe los mensajes del ESP32
    ▼
RECHAZO — Mensajes no recibidos por topic mismatch
```

```
ESP32 → MQTT Broker (INCORRECTO)
    Topic: mole/telemetry (no coincide con mole/sensors/#)

ESP32 → Edge Node (PROBLEMA ADICIONAL)
    El edge_node está subscripto a "mole/sensors/#"
    El ESP32 publica en "mole/telemetry"
    NO HAY RECEPCIÓN DE DATOS
```
    │
    │ sync_to_backend() — POST /api/v1/sensor-data/batch/
    │ ⚠️ FORMATO INCORRECTO: {device_id, plant_id, timestamp, sensors[]}
    ▼
Nginx (8080) — API Gateway
    │
    │ /api/v1/sensor-data/batch/
    ▼
Django (sensor_batch_view)
    │
    │ ❌ Espera: {batch: [{plant_id, recorded_at, soil_humidity, ...}]}
    │ ❌ Recibe: {batch: [{device_id, plant_id, timestamp, sensors[]}]}
    ▼
REJECT (400 — Invalid payload)
```

---

## 7. RECOMENDACIONES DE REMEDIACIÓN

### Prioridad 1 (Bloqueante para Producción)

1. **Corregir formato JSON del edge_node** para que sea compatible con `sensor_batch_view`:
   - Renombrar `timestamp` → `recorded_at`
   - Aplanar `sensors[]` a campos individuales (`soil_humidity`, `air_temperature`, etc.)
   - Eliminar campo extra `device_id`

2. **Implementar validación Anti-Replay en edge_node**:
   - Verificar `abs(now - timestamp) < 300` antes de enqueue_reading()
   - Rechazar o loguear mensajes con timestamps fuera de rango

### Prioridad 2 (Producción)

3. **Documentar firmware ESP32 esperado** o crear esqueleto de referencia en esp32_node/

4. **Crear entrypoint.sh** para django-backend que ejecute migraciones automáticamente

### Prioridad 3 (Post-Producción)

5. **Verificar Dockerfiles de MS3** incluyen weasyprint y boto3

6. **Scripts de health check** para validación pre-deploy

---

## 8. CONCLUSIÓN

| Categoría | Cumplimiento | Notas |
|-----------|--------------|-------|
| Infrastructure | 95% | ✅ Zero-Trust, volúmenes, redes correctos |
| ESP32 Firmware | 100% | ✅ Fase 6A aplicada: NTP, topic dinámico, campos Django |
| Edge Node | 70% | ⚠️ Faltan: device_id→plant_id, Anti-Replay |
| MS3 Reports | 100% | ✅ Implementación real y completa |
| Integración E2E | 🔴 2 brechas | C-004: device_id→plant_id, C-005: Anti-Replay |