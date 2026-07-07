# esp32_node — Firmware de Nodo IoT Mole.AI

## 1. Overview

`esp32_node` es el firmware embebido para el nodo de borde (ESP32) del ecosistema Mole.AI. Su función es capturar telemetría de sensores ambientales y de suelo, empaquetarla en un payload compacto (formato `edge-batch`), y enviarla al backend `core_backend` para almacenamiento, análisis predictivo y control de riego.

### Propósito

- **Capa de borde**: ejecuta lectura de sensores y transmisión sin depender de conectividad continua.
- **Payload compacto**: formato `{ts, ri, a:{t,h,l,u}, s:[{p,v}]}` (~180 bytes) diseñado para redes rurales de bajo ancho de banda.
- **Dual provisioning**: BLE (NimBLE) + Captive Portal (WiFi AP + HTTP) para configuración inicial.
- **Store & forward**: buffer offline circular para resiliencia ante cortes de red.

## 2. Arquitectura

```
┌──────────────────────────────────────────────────────────┐
│                      ESP32 (ESP-IDF 5.2)                  │
│                                                           │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐             │
│  │  DHT20   │   │  LTR390  │   │  Soil×N   │             │
│  │ (I2C:38) │   │ (I2C:53) │   │(ADC1:32,33)│             │
│  └────┬─────┘   └────┬─────┘   └─────┬─────┘             │
│       └──────────────┼───────────────┘                    │
│                      ↓                                    │
│              ┌───────────────┐                             │
│              │  WiFi event   │                             │
│              │  → post queue │                             │
│              └───────┬───────┘                             │
│                      ↓ (event)                             │
│              ┌───────────────┐                             │
│              │    FSM Task   │  xQueueReceive blocking     │
│              │  (12 estados) │←─────────────────────┐      │
│              └───────┬───────┘                      │      │
│                      ↓ (action)                ┌────┴─────┐│
│              ┌───────────────┐                  │Transport ││
│              │  Payload      │                  │Layer     ││
│              │  Builder      │                  │(HTTP)    ││
│              │  (edge_frame) │                  └──────────┘│
│              └───────┬───────┘                              │
│                      ↓                                      │
│              ┌───────────────┐                              │
│              │    Offline    │                              │
│              │    Buffer     │                              │
│              │  (30 slots)   │                              │
│              └───────────────┘                              │
└──────────────────────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────┐
│                    core_backend                           │
│  POST /api/v1/sensor-data/edge-batch/ (Bearer token)      │
└──────────────────────────────────────────────────────────┘
```

## 3. Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| MCU | ESP32 (Xtensa dual-core LX6) |
| Framework | ESP-IDF 5.2.1 |
| RTOS | FreeRTOS (ESP-IDF fork) |
| BLE | NimBLE (host-only) |
| WiFi | ESP-WiFi (esp_wifi.h) |
| HTTP Client | esp_http_client (ESP-IDF) |
| JSON | cJSON 1.7.19 (managed) |
| NVS | nvs_flash (encrypted partition) |
| ADC | ADC1 oneshot (ESP-IDF 5.x API) |
| I2C | I2C master (ESP-IDF 5.x) |
| Timestamp | SNTP triple-redundant (pool.ntp.org, time.google.com, time.cloudflare.com) |

## 4. Hardware

| Sensor | Bus | Address/Pin | LED | Descripción |
|--------|-----|-------------|-----|-------------|
| DHT20 | I2C | `0x38` | ✅ | Temp (°C) + Humedad (%) |
| LTR390 | I2C | `0x53` | ❌ | UV Index + Lux |
| Soil #1 | ADC1 | GPIO32 | ❌ | Humedad de suelo (%) |
| Soil #2 | ADC1 | GPIO33 | ❌ | Humedad de suelo (%) |
| I2C SDA | I2C | GPIO21 | — | Bus I2C |
| I2C SCL | I2C | GPIO22 | — | Bus I2C |

## 5. Máquina de Estados (FSM)

```
COLD_START ──→ NVS_LOADING ──→ PROVISIONING ──→ WIFI_CONNECT
                                    ↑                 ↓ connected
                                    │            NTP_SYNC
                                    │                 ↓
                                    │           SENSOR_INIT
                                    │          ╱ full     ╲ partial
                                    │         ↓            ↓
                                    │    TRANSPORT    TELEMETRY_
                                    │    CONNECTING   DEGRADED
                                    │         ↓            ↓
                                    │    TELEMETRY_SENDING ←─┘
                                    │         ↓ send OK
                                    │    DEEP_SLEEP ──→ COLD_START
                                    │
                                    │    WiFi/Transport drop ↓
                                    │    RECONNECTING (backoff 1..30s)
                                    │         ↓ max attempts
                                    │    DEEP_SLEEP
                                    │
                                    │    ERROR ──→ REBOOT ──→ COLD_START
                                    └──────────────────────────┘
```

**Constantes de configuración:**

| Constante | Valor | Propósito |
|-----------|-------|-----------|
| `RECONNECT_MAX_ATTEMPTS` | 5 | Reintentos antes de buffer offline |
| `OFFLINE_BUFFER_SIZE` | 30 | Tamaño de cola circular |
| `OFFLINE_OVERFLOW_POLICY` | DROP_OLDEST | Política de descarte |
| `WIFI_RECONNECT_TIMEOUT_MS` | 30000 | Timeout de reconexión WiFi |
| `TRANSPORT_RECONNECT_TIMEOUT_MS` | 10000 | Timeout de reconexión HTTP |
| `TELEMETRY_INTERVAL_MS` | 300000 | Intervalo entre envíos (5 min) |

## 6. Formato de Payload (edge-batch)

```json
{
  "ts": 1699123456.789,
  "ri": 5,
  "a": {
    "t": 28.4,
    "h": 65.2,
    "l": 410.0,
    "u": 5.5
  },
  "s": [
    {"p": "32", "v": 2847},
    {"p": "33", "v": 3012}
  ],
  "dg": 0
}
```

| Campo | Tipo | Rango | Descripción |
|-------|------|-------|-------------|
| `ts` | Float (epoch) | > 0 | Unix timestamp UTC |
| `ri` | Integer | [1, 120] | Report interval en minutos |
| `a.t` | Float | [-40, 80] | Air temperature (°C) |
| `a.h` | Float | [0, 100] | Air humidity (%) |
| `a.l` | Float | [0, 65535] | Light level (lux) |
| `a.u` | Float | [0, 15] | UV Index |
| `s[].p` | String | max 10 chars | Hardware pin ID (CharField en core_backend ✅) |
| `s[].v` | Float | [0, 4095] | Soil ADC raw value |
| `dg` | Integer (opcional) | [0, 15] | Degraded bitmask: `~ambient_valid & 0x0F`. Ignorado por core_backend, guardado en NVS para diagnóstico local |

## 7. Endpoints core_backend

| Método | Path | Auth | Propósito |
|--------|------|------|-----------|
| POST | `/api/v1/sensor-data/edge-batch/` | Bearer token (Device.auth_token) | Payload compacto ESP32 |
| POST | `/api/v1/sensor-data/batch/` | X-Hardware-Api-Key | Buffer offline batch |
| GET | `/api/v1/devices/{id}/health/` | JWT Supabase | Dashboard de salud del nodo |

## 8. Deuda Técnica

| ID | Deuda | Impacto | Archivo | Estado |
|----|-------|---------|---------|--------|
| TD-01 | Dirección I2C LTR390 incorrecta (0x1C en vez de 0x53) | **Crítico** | `sensor_ltr390.c:20` | ✅ VS1a |
| TD-02 | Sin reconexión | **Crítico** | `main.c` | ✅ VS1b+VS2+VS3 |
| TD-03 | portMAX_DELAY en provisioning | **Alto** | `ble_provisioning.c` | ✅ VS5 |
| TD-04 | Sin buffer offline | **Alto** | `offline_buffer.c` | ✅ VS4 |
| TD-05 | Payload incompatible | **Alto** | `payload_builder.c` | ✅ VS1a |
| TD-06 | Reconexión sin backoff | **Medio** | `main.c` | ✅ VS3 |
| TD-07 | cJSON_Print heap alloc | **Medio** | `payload_builder.c` | ✅ VS1a |
| TD-08 | ESP_ERROR_CHECK en sensores | **Medio** | `main.c` | ✅ VS2 |
| TD-09 | URI hardcodeada en Kconfig | **Bajo** | `Kconfig.projbuild` | ⚠️ Pendiente |
| TD-10 | TWDT no reseteado | **Medio** | `main.c` | ✅ VS7c |

## 9. Bugs Identificados

| ID | Bug | Severidad | Archivo | Detalle | Estado |
|----|-----|-----------|---------|---------|--------|
| BUG-01 | LTR390 address 0x1C → debe ser 0x53 | **Crítica** | `sensor_ltr390.c:20` | Sensor UV nunca funciona; fallback MOCK enmascara | ✅ VS1a |
| BUG-02 | Curve25519 usado donde se declara Ed25519 | **Crítica** | `auditFW.md CRIT-SEC-06` | ECDH ≠ EdDSA; firmas inválidas | ✅ VS2 (mole_identity removido del build) |
| BUG-03 | NVS encryption configurada pero flash encryption deshabilitada | **Crítica** | `auditFW.md CRIT-SEC-02` | Claves NVS en texto plano | ⚠️ Pendiente (HW security) |
| BUG-04 | portMAX_DELAY en provisioning + WiFi connect | **Alta** | `main.c` | Nodo zombie si app nunca escribe o AP no responde | ✅ VS5 |
| BUG-05 | memset(priv_buf) optimizable por compilador | **Alta** | `auditFW.md CRIT-SEC-03` | Dead store en producción con -Os | ⚠️ Pendiente (mole_identity removido) |

## 10. Compliance

| Norma | Estado | Notas |
|-------|--------|-------|
| **ETSI EN 303 645** | ⚠️ Parcial | SNTP triple OK; backoff exponencial + buffer offline implementados; BLE provisioning en SECURITY_0 (debe ser SECURITY_1) — pendiente upgrade HW security |
| **LFPDPPP** | ⚠️ Parcial | Timestamps UTC sin PII; payload sin datos personales |

## 11. Tests

- **Framework**: tests C puros con assert (host), compilados con gcc nativo
- **Tests de dominio** (host, TDD): **37 tests total** — 8 payload_builder + 15 state_machine enum + 8 state_machine behavior + 6 offline_buffer
- **Tests HW** (pendientes): provisioning BLE, WiFi connect/reconnect, envío edge-batch, deep sleep cycle
- **Mock backend**: `python3 mock_backend.py` (servidor HTTP que simula core_backend para pruebas HW)
- **Makefile targets**: `test_payload_builder`, `test_state_machine`, `test_fsm_behavior`, `test_offline_buffer`
- **Stubs**: `tests/stubs/` — FreeRTOS, ESP-IDF headers, y `main_stubs.c` para testear state_machine y offline_buffer en host
