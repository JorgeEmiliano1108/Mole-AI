# Modelo de datos y base de datos

## Propósito
Definir de forma estructurada el modelo de datos utilizado por MOLE‑AI, describiendo los conceptos conceptuales, lógicos y físicos, así como las relaciones, índices y políticas de integridad que garantizan la consistencia y la trazabilidad del sistema.

## Modelo conceptual
- **Usuario**: actor que interactúa con la plataforma (agricultor, técnico o administrador).
- **Planta**: entidad que representa una planta cultivada por un usuario.
- **Especie**: catálogo taxonómico de plantas y cultivos.
- **Dispositivo IoT**: ESP32 que captura datos de sensores y los envía al backend.
- **Lectura ambient**: datos de temperatura, humedad, luz, UV asociados a un dispositivo.
- **Lectura de suelo**: datos de humedad y pH asociados a una pin de hardware vinculada a una planta.
- **Embeddings / Conocimiento botánico**: fragmentos de texto extraídos de PDFs, vectorizados y almacenados para RAG.
- **Diagnóstico IA**: resultado de la inferencia de visión (especie, condición, severidad, confianza, pH estimado).
- **Reporte**: documento PDF generado a partir de datos de sensores.
- **Auditoría**: registro inmutable de acciones críticas del sistema.
- **Feedback**: tickets de retroalimentación enviados por usuarios.

## Modelo lógico (Django ORM → PostgreSQL)
| Tabla (modelo) | Campos clave | Relaciones | Índices / restricciones |
|-----------------|--------------|------------|--------------------------|
| **users** | `id (PK)`, `username`, `email`, `supabase_uid`, `is_superuser`, `is_staff`, `is_active`, `avatar_url`, `phone_number`, `is_premium`, `data_consent`, `is_email_verified` | Ninguna externa directa (FK hacia otros modelos). | `unique(email)`, `unique(supabase_uid)` |
| **devices** | `id (UUID PK)`, `owner_id (FK → users)`, `name`, `auth_token (unique)`, `status`, `last_seen`, `report_interval_minutes`, `is_active` | `owner_id` → `users` | `unique(auth_token)`, `index(is_active)`, `index(last_seen)` |
| **hardware_bindings** | `id (PK)`, `device_id (FK → devices)`, `hardware_pin`, `plant_id (FK → user_plants)` | `device_id` → `devices`; `plant_id` → `user_plants` | `unique_together(device_id, hardware_pin)` |
| **ambient_readings** | `id (PK)`, `device_id (FK → devices)`, `recorded_at`, `air_temperature`, `air_humidity`, `light_level`, `uv_index` | `device_id` → `devices` | `index(device_id, recorded_at)` |
| **soil_readings** | `id (PK)`, `binding_id (FK → hardware_bindings)`, `recorded_at`, `soil_humidity`, `ph_level` | `binding_id` → `hardware_bindings` | `index(binding_id, recorded_at)` |
| **hourly_ambient_aggregates** | `id (PK)`, `device_id (FK)`, `hour`, `avg_air_temperature`, `avg_air_humidity`, `avg_uv_index`, `avg_light_level`, `sample_count` | `device_id` → `devices` | `unique_together(device_id, hour)`, `index(hour)` |
| **hourly_soil_aggregates** | `id (PK)`, `binding_id (FK)`, `hour`, `avg_soil_humidity`, `min_soil_humidity`, `max_soil_humidity`, `sample_count` | `binding_id` → `hardware_bindings` | `unique_together(binding_id, hour)`, `index(hour)` |

| **user_plants** | `id (UUID PK)`, `user_id (FK → users)`, `species_id (FK → species_catalog)`, `nickname`, `created_at`, … | `user_id` → `users`; `species_id` → `species_catalog` | `index(user_id)`, `index(species_id)` |
| **species_catalog** | `id (PK)`, `scientific_name`, `common_name`, `description`, `category`, `ideal_humidity_min`, `ideal_humidity_max`, `ideal_temp_min`, `ideal_temp_max`, `ideal_ph_min`, `ideal_ph_max`, `is_protected_nom059`, `protection_category` | Ninguna | `unique(scientific_name)` |
| **botanical_knowledge** | `id (PK)`, `content`, `source_url`, `chunk_metadata (JSON)`, `embedding (vector(1536))` | Ninguna | GIN index on `embedding` (pgvector) |
| **ai_diagnostics** | `id (UUID PK)`, `user_id (FK nullable → users)`, `plant_id (FK → user_plants)`, `analyzed_at`, `image_path`, `diagnosis_label`, `confidence_score`, `metadata (JSON)` | `user_id` → `users` (nullable); `plant_id` → `user_plants` | `index(plant_id)`, `index(analyzed_at)` |
| **diagnosticos_geolocalizados** | `id (PK)`, `diagnostic_id (FK → ai_diagnostics)`, `user_id (FK nullable)`, `condition_name`, `latitude`, `longitude`, `severity`, `metadata (JSON)`, `created_at` | `diagnostic_id` → `ai_diagnostics` | `index(latitude, longitude)` |
| **feedback_tickets** | `id (PK)`, `user_id (FK nullable)`, `topic`, `message`, `status`, `created_at` | `user_id` → `users` (nullable) | `index(user_id)`, `index(status)` |
| **audit_logs** | `id (PK)`, `user_id`, `action`, `timestamp`, `ip_address`, `details` | Ninguna | `index(timestamp)`.  Operaciones `save` y `delete` están prohibidas (inmutabilidad). |
| **telemetry_archives** | `id (PK)`, `device_id (FK)`, `period_start`, `period_end`, `s3_key (unique)`, `rows_archived`, `created_at` | `device_id` → `devices` | `unique(s3_key)`, `index(period_start, period_end)` |


*Nota: la tabla **users** corresponde a la tabla física **auth_users** en la base de datos PostgreSQL.*

## Deuda técnica / Legacy

| Tabla | Descripción | Comentario |
|------|------------|------------|
| **sensor_logs** (legacy) | Registros históricos de sensores sin FK, solo lectura. | Conservado por migraciones históricas; no forma parte del modelo lógico activo. |
| **iot_nodes** (legacy) | Información de nodos de borde vinculados a usuarios. | No usado en la lógica actual; se mantiene solo como referencia histórica. |

## Modelo físico
Todos los modelos se materializan en PostgreSQL 13+ con la extensión **pgvector** habilitada.  Los tipos de datos críticos son:
- `UUID` para identificadores de dispositivos y plantas.
- `JSONB` para `metadata` en diagnósticos y `chunk_metadata` en conocimiento botánico.
- `vector(1536)` para embeddings de texto, con índice GIN (`vector_cosine_ops`).
- `TIMESTAMP WITH TIME ZONE` (UTC) para marcas de tiempo.
- `BOOLEAN` para flags de consentimiento y verificación de correo.


*Este diccionario está intencionalmente parcial; incluye solo los campos críticos para la comprensión del modelo.*

## Índices críticos
- GIN index sobre `botanical_knowledge.embedding` (vector_cosine_ops) para búsquedas semánticas.
- Índices compuestos `index(device_id, recorded_at)` y `index(binding_id, recorded_at)` para lecturas de telemetría.
- Índices únicos en `devices.auth_token`, `species_catalog.scientific_name` y `telemetry_archives.s3_key`.
- Índice temporal en `audit_logs.timestamp` para consultas de auditoría.

## Políticas de integridad
- **FK ON DELETE SET NULL** en `ai_diagnostics.user_id` y `feedback_tickets.user_id` para preservar datos científicos al eliminar usuarios.
- **Soft‑delete** en `devices.is_active` mediante flag; los datos históricos de `devices` permanecen inalterables.
- **Auditoría inmutable**: tabla `audit_logs` prohíbe `UPDATE` y `DELETE` mediante excepciones en el modelo.
- **Retención**: Los chunks en `botanical_knowledge` pueden ser purgados mediante tareas programadas (no implementado aún).  Los archivos PDF y reportes en S3 se conservan 30 días tras la generación.

## Seguridad de datos
- Todos los campos que contienen PII (`email`, `phone_number`, `avatar_url`) están sujetos a enmascaramiento al realizar borrado de cuenta (ARCO).  Los datos de sensores, diagnósticos y conocimiento botánico no son considerados PII.
- Las comunicaciones con AWS S3 y NVIDIA NIM se realizan mediante TLS.
- Los accesos a la base de datos están restringidos a la red interna (`mole_internal`) y a credenciales gestionadas por Docker secrets.

## Diccionario de datos (intencionalmente parcial)
- **users.id** – UUID del usuario.
- **users.username** – Nombre de usuario único.
- **users.email** – Correo electrónico (único).
- **devices.id** – UUID del dispositivo hardware.
- **devices.auth_token** – Token de autenticación del dispositivo (string).
- **ambient_readings.air_temperature** – Temperatura del aire (°C).
- **soil_readings.soil_humidity** – Humedad del suelo (%).
- **botanical_knowledge.embedding** – Vector de embeddings de texto.
- **ai_diagnostics.diagnosis_label** – Texto que describe la condición detectada por visión.
- **audit_logs.action** – Descripción textual de la acción auditada (p.ej., `DELETE_ACCOUNT_ARCO`).
- **telemetry_archives.s3_key** – Ruta del objeto en AWS S3 que contiene el archivo exportado.


