# Requisitos del Firmware ESP32 Node

## 1. Requisitos Funcionales

### 1.1 Provisioning y Configuración

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-01 | Provisioning BLE | Recibir credenciales WiFi + device token por BLE (UUID 0xFEE0/0xFEE1) | Alta | ✅ Cumple | ble_provisioning.c |
| RF-02 | Provisioning WiFi AP | Modo AP con captive portal HTTP para configuración manual | Alta | ✅ Cumple | main.c |
| RF-03 | Persistencia NVS | Guardar credenciales en NVS cifrado con validación en cada boot | Alta | ✅ Cumple | main.c |
| RF-04 | Reprovisioning | Mecanismo para forzar re-provisioning (HW reset o señal BLE) | Media | ❌ No cumple | ble_provisioning.c |
| RF-05 | Timeout Provisioning | Timeout de 5 min en BLE + captive portal, deep sleep si inactivo | Media | ✅ Cumple | main.c |

### 1.2 Lectura de Sensores

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-06 | Lectura DHT20 | Temperatura (°C) y humedad (%) vía I2C | Alta | ✅ Cumple | sensor_dht20.c |
| RF-07 | Lectura LTR390 | UV Index y lux vía I2C | Alta | ✅ Cumple | sensor_ltr390.c |
| RF-08 | Lectura Suelo | Humedad de suelo (%) vía ADC (GPIO32,33) | Alta | ✅ Cumple | sensor_soil.c |
| RF-09 | Validación Rangos | Rechazar lecturas fuera de rango físico | Media | ⚠️ Parcial | sensores/*.c |
| RF-10 | Degradación Sensores | Fallback a MOCK si sensor no responde | Media | ✅ Cumple | main.c |

### 1.3 Conectividad

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-11 | Conexión WiFi STA | Conectar a AP con credenciales guardadas | Alta | ✅ Cumple | main.c |
| RF-12 | Reconexión WiFi | Reconexión automática con backoff exponencial | Alta | ✅ Cumple | main.c |
| RF-13 | Sincronización NTP | SNTP triple-redundante con timeout 10s | Alta | ✅ Cumple | mole_ntp.c |
| RF-14 | Envío HTTP REST | POST a edge-batch con payload compacto + `dg` bitmask | Alta | ✅ Cumple | main.c/transport_layer.c |
| RF-15 | Autenticación Bearer | Header Authorization: Bearer <device_token> | Alta | ✅ Cumple | main.c |
| RF-16 | Buffer Offline | Cola circular de 30 muestras para envío diferido | Alta | ✅ Cumple | offline_buffer.c |

### 1.4 Telemetría

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-17 | Payload edge-batch | Formato compacto {ts, ri, a:{t,h,l,u}, s:[{p,v}], dg} | Alta | ✅ Cumple | payload_builder.c |
| RF-18 | Intervalo Configurable | Intervalo de telemetría configurable vía provisioning | Media | ✅ Cumple | main.c |
| RF-19 | Degraded Flag | Incluir `dg` bitmask en payload indicando sensores en fallo | Media | ✅ Cumple | payload_builder.c |
| RF-20 | Deep Sleep | Deep sleep entre envíos (5 min default) | Alta | ✅ Cumple | main.c |
| RF-21 | TWDT Reset | Reseteo de watchdog antes de deep sleep | Media | ✅ Cumple | main.c |

## 2. Requisitos No Funcionales

### 2.1 Seguridad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-01 | BLE Provisioning Seguro | Cifrado en provisioning (mínimo SECURITY_1) | Alta | ❌ No cumple | Usa SECURITY_0 |
| RNF-02 | Flash Encryption | Cifrado de flash para proteger NVS keys | Alta | ❌ No cumple | Configurada pero no activa |
| RNF-03 | Zeroize Claves | Limpieza segura de material criptográfico en RAM | Alta | ⚠️ Parcial | usa memset, no platform_zeroize |
| RNF-04 | Bearer Token Seguro | Token almacenado en NVS cifrado | Alta | ⚠️ Parcial | NVS encrypt config pero flash encrypt no |
| RNF-05 | Anti-Replay Timestamp | Timestamp con tolerancia ±65s en endpoint individual | Media | ❌ No cumple | edge-batch acepta pasado |

### 2.2 Resiliencia

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-06 | Reconexión Backoff | Backoff exponencial (1s→2s→4s→...→30s) en WiFi y Transport | Alta | ✅ Cumple | FreeRTOS timer + NVS persist |
| RNF-07 | Buffer Offline | Almacenar hasta 30 muestras sin conexión | Alta | ✅ Cumple | offline_buffer.c: cola circular 30 slots, DROP_OLDEST |
| RNF-08 | Timeout Provisioning | Timeout finito (5 min) en BLE y captive portal | Alta | ✅ Cumple | MOLE_PROV_TIMEOUT_MS |
| RNF-09 | Degradación Gradual | Operación parcial si sensor falla | Media | ✅ Cumple | FSM_TELEMETRY_DEGRADED + dg bitmask |
| RNF-10 | TWDT Management | Reseteo de watchdog en cada ciclo de telemetría | Media | ✅ Cumple | esp_task_wdt_reset() antes de fsm_dispatch() |

### 2.3 Performance

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-11 | Payload Compacto | Payload < 200 bytes | Alta | ✅ Cumple | edge_frame ~180 bytes |
| RNF-12 | Heap Control | Usar cJSON_PrintPreallocated con buffer estático | Media | ✅ Cumple | payload_builder con buffer 512 bytes |
| RNF-13 | Stack Adecuado | Stack fsm_task ≥ 6KB | Media | ✅ Cumple | Stack 6144 bytes |
| RNF-14 | WiFi Power Save | WIFI_PS_NONE para latencia mínima de reconexión | Media | ✅ Cumple | esp_wifi_set_ps(WIFI_PS_NONE) |
| RNF-15 | I2C Retry | Reintentos en lecturas I2C (3 intentos) | Media | ❌ No cumple | Sin retry |

### 2.4 Mantenibilidad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-16 | Máquina de Estados Explícita | FSM con 13 estados, 20 eventos, transiciones definidas | Alta | ✅ Cumple | state_machine.c — tabla de transiciones en flash |
| RNF-17 | Separación Transporte/Payload | Módulo TransportLayer y PayloadBuilder independientes | Alta | ✅ Cumple | transport_layer.c, payload_builder.c, offline_buffer.c |
| RNF-18 | Comunicación por Cola FreeRTOS | TransportLayer notifica a FSM vía QueueHandle_t, no punteros directos | Alta | ✅ Cumple | transport_layer.c + FSM QueueHandle_t events |
| RNF-18 | Tests de Dominio en Host | Tests para payload_builder (8), FSM (23), offline_buffer (6) | Media | ✅ Cumple | 37 tests host, 4 targets Makefile |
| RNF-19 | URI Configurable sin Recompilar | URI de backend configurable vía NVS/menuconfig | Media | ⚠️ Parcial | Kconfig requiere recompilar |

## 3. Deuda Técnica

| ID | Deuda | Impacto | Prioridad | Módulo | Acción Recomendada |
|----|-------|---------|-----------|--------|-------------------|
| TD-01 | LTR390 address 0x1C | **Crítico** — sensor no detectado | Alta | sensor_ltr390.c | ✅ Corregido a 0x53 (VS1a) |
| TD-02 | Sin reconexión WS | **Crítico** — pérdida total | Alta | main.c | ✅ FSM + backoff (VS1b+VS2+VS3) |
| TD-03 | portMAX_DELAY | **Alto** — nodo zombie | Alta | main.c | ✅ MOLE_PROV_TIMEOUT_MS (VS5) |
| TD-04 | Sin buffer offline | **Alto** — pérdida rural | Alta | offline_buffer.c | ✅ Cola circular 30 slots (VS4) |
| TD-05 | Payload incompatible | **Alto** — no llega a backend | Alta | main.c | ✅ edge_frame_t + payload_builder (VS1a) |
| TD-06 | Backoff fijo 2s | **Medio** — saturación RF | Media | main.c | ✅ Backoff exp. + jitter (VS3) |
| TD-07 | cJSON_Print heap | **Medio** — fragmentación | Media | main.c | ✅ PrintPreallocated 512B (VS1a) |
| TD-08 | ESP_ERROR_CHECK en sensores | **Medio** — abort en fallo | Media | main.c | ✅ Degradación graceful (VS2) |
| TD-09 | URI hardcodeada | **Bajo** — rigidez | Baja | Kconfig | ⚠️ Pendiente — requiere NVS override |
| TD-10 | Sin TWDT reset | **Medio** — wake prematuro | Media | main.c | ✅ esp_task_wdt_reset/delete (VS7c) |

## 4. Bugs Identificados

| ID | Bug | Severidad | Módulo | Causa Raíz | Solución Propuesta |
|----|-----|-----------|--------|-----------|-------------------|
| BUG-01 | LTR390 address | **Crítica** | sensor_ltr390.c | Constante 0x1C incorrecta | Cambiar a 0x53 (datasheet) — ✅ Corregido en VS1a |
| BUG-02 | Curve25519 ≠ Ed25519 | **Crítica** | mole_identity.c | ECDH usado donde se necesita EdDSA | Migrar a libsodium |
| BUG-03 | Flash encryption off | **Crítica** | sdkconfig | NVS encrypt config pero flash encrypt no | Habilitar en sdkconfig |
| BUG-04 | memset optimizable | **Alta** | mole_identity.c | Dead store en -Os | Usar mbedtls_platform_zeroize |

## 5. Cumplimiento Normativo

| Norma | Estado | Evidencia | Brecha |
|-------|--------|-----------|--------|
| **ETSI EN 303 645** | ⚠️ Parcial | SNTP triple-redundante implementado | BLE en SECURITY_0, sin autenticación WS, sin backoff exponencial |
| **LFPDPPP** | ⚠️ Parcial | Payload sin PII, timestamps UTC | No hay política de retención de datos locales en buffer offline |
