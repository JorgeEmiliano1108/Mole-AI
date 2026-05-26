# Auditoría de Firmware — Mole.AI OpenClaw Node v2.1.0

**Fecha:** 2026-04-25  
**Auditor:** Antigravity — Senior Embedded Firmware Engineer  
**Target:** ESP-IDF 5.2.1 / FreeRTOS / ESP32 (Xtensa dual-core)  
**Alcance:** `microservices/esp32_node/` — 7 archivos fuente, 6 headers, partitions.csv, sdkconfig

---

## 1. Auditoría de FreeRTOS y Memoria

### 1.1 Riesgo de Stack Overflow en `xTaskCreate`

| Tarea | Archivo | Línea | Stack (bytes) | Riesgo |
|---|---|---|---|---|
| `mole_telem` | `mole_openclaw.c` | L115 | 4096 | **MEDIO** |

**Hallazgo CRIT-MEM-01:** La tarea `telemetry_task` se crea con 4096 bytes de stack (`mole_openclaw.c:115`). Actualmente el cuerpo del loop solo hace `ESP_LOGI`, pero si en el futuro se invoca `handle_sensor_read` (que construye objetos cJSON, lee I2C y formatea JSON), el consumo real superará los 4096 bytes. Lecturas I2C + cJSON en stack pueden alcanzar ~3KB fácilmente.

**Mitigación:** `CONFIG_FREERTOS_CHECK_STACKOVERFLOW_CANARY=y` está activo en sdkconfig (L1243), lo cual es correcto — detectará overflow con canary pattern. Sin embargo, `CONFIG_FREERTOS_WATCHPOINT_END_OF_STACK` está deshabilitado (L1264). Habilitar ambos proporciona detección por hardware + software.

**Recomendación:** Aumentar stack a 6144 bytes y habilitar `CONFIG_FREERTOS_WATCHPOINT_END_OF_STACK=y`.

### 1.2 Liberación de Memoria Dinámica (cJSON)

**Hallazgo CRIT-MEM-02:** En `handle_sensor_read()` (`mole_openclaw.c:35-57`):

```c
cJSON *root = cJSON_CreateObject();          // L35 — alloc heap
// ... populate ...
*out_payload_json = cJSON_PrintUnformatted(root);  // L56 — alloc heap (caller must free)
cJSON_Delete(root);                                // L57 — freed ✓
```

`cJSON_Delete(root)` libera el árbol JSON correctamente. Sin embargo, `cJSON_PrintUnformatted()` retorna un `char*` alocado con `cJSON_malloc()`. **La responsabilidad de liberar `*out_payload_json` recae enteramente en la API de `esp-openclaw-node`**. Si el framework OpenClaw no invoca `cJSON_free()` o `free()` sobre ese puntero después de transmitirlo por WebSocket, se producirá un **memory leak de ~200-500 bytes por cada invocación de `sensor.read`**.

**Riesgo:** ALTO — leak acumulativo en dispositivo de larga operación (24/7). Con telemetría cada 5 min = ~576 invocaciones/día × ~300 bytes = **~170 KB/día de leak potencial**.

**Recomendación:** Verificar en documentación de `esp-openclaw-node` que `out_payload_json` sea liberado. Si no, envolver en wrapper que haga `free()` post-transmisión.

### 1.3 Objetos mbedTLS nunca liberados

**Hallazgo CRIT-MEM-03:** En `mole_identity_init()` (`mole_identity.c:86-88`):

```c
mbedtls_pk_init(&id->pk);
mbedtls_entropy_init(&id->entropy);
mbedtls_ctr_drbg_init(&id->drbg);
```

No existe función `mole_identity_deinit()`. Los contextos `mbedtls_pk_context`, `mbedtls_entropy_context`, y `mbedtls_ctr_drbg_context` **nunca se liberan** con sus respectivos `mbedtls_pk_free()`, `mbedtls_entropy_free()`, `mbedtls_ctr_drbg_free()`. Grep confirma: **cero llamadas a `mbedtls_*_free` en todo el codebase**.

**Riesgo:** MEDIO — la identidad vive todo el ciclo de vida del firmware, así que en operación normal no es un leak activo. Pero si `mole_identity_init` falla parcialmente (e.g., en L114, L125), se hace `free(id)` sin liberar los contextos mbedTLS previamente inicializados.

### 1.4 Allocaciones sin liberación en error paths de sensores

**DHT20** (`sensor_dht20.c:55-58`): Si `i2c_master_bus_add_device` falla, se hace `free(s)` ✓. Correcto.

**LTR390** (`sensor_ltr390.c:82,89`): `free(s)` en ambos error paths ✓. Correcto.

**Soil** (`sensor_soil.c:36,44-47`): `free(s)` + `adc_oneshot_del_unit()` en error de config ✓. Correcto.

---

## 2. Robustez de la Capa PHY e I2C

### 2.1 Discrepancia de Dirección I2C — LTR390

**Hallazgo CRIT-I2C-01:** Existe conflicto entre la dirección declarada en el contexto del usuario (`0x1C`) y el código:

- `mole_config.h:34` → `#define MOLE_LTR390_ADDR 0x53`
- `sensor_ltr390.c:20` → `#define LTR390_ADDR 0x1C`

**El driver usa `0x1C` (L20) pero `mole_config.h` declara `0x53`.** La constante en `mole_config.h` es cosmética (no se usa en el driver). La dirección real del LTR-390UV-01 según datasheet rev 1.1 es **`0x53`**. El valor `0x1C` en el driver es **INCORRECTO** y causará fallo de inicialización en hardware real (Part ID mismatch).

**Impacto:** CRÍTICO — el sensor UV nunca funcionará en hardware real. El fallback a MOCK en `main.c:218-222` enmascara este bug.

### 2.2 Ausencia de Mutex en Bus I2C Compartido

**Hallazgo CRIT-I2C-02:** DHT20 (`0x38`) y LTR390 comparten `I2C_NUM_0`. En `handle_sensor_read()` (`mole_openclaw.c:40-50`), se leen ambos sensores secuencialmente **sin protección de mutex**. Si `telemetry_task` y un comando entrante `sensor.read` ejecutan lecturas simultáneamente, las transacciones I2C se intercalarán, corrompiendo datos y potencialmente bloqueando el bus.

**Nota:** El driver `i2c_master` de ESP-IDF 5.x proporciona serialización interna por bus, lo que mitiga parcialmente. Sin embargo, la lectura del LTR390 involucra **cambio de modo** (ALS→UVS, `sensor_ltr390.c:109,121`) con 100ms de espera entre cada uno. Si otra tarea lee DHT20 durante esa ventana de 100ms, el cambio de contexto del LTR390 puede resultar en datos inconsistentes.

**Recomendación:** Implementar `SemaphoreHandle_t` para serializar acceso al bus I2C a nivel de aplicación.

### 2.3 Sin Reintentos en Lecturas I2C

**Hallazgo WARN-I2C-03:** Las funciones `sensor_dht20_read()` y `sensor_ltr390_read()` no implementan reintentos. Un solo NACK en un bus I2C ruidoso (cableado agrícola, interferencia EMI) produce fallo inmediato.

- `sensor_dht20.c:76` — `i2c_master_transmit(..., 100)` timeout 100ms, sin retry.
- `sensor_ltr390.c:53` — `i2c_master_transmit(dev, buf, 2, 100)` sin retry.

### 2.4 Sin Validación de Rango en Lecturas

**Hallazgo WARN-I2C-04:**

- **DHT20** (`sensor_dht20.c:109-110`): Valores de temperatura y humedad se calculan sin validar rango. DHT20 opera en -40°C a 80°C. Valores fuera de rango deben marcarse como inválidos.
- **Soil** (`sensor_soil.c:69-70`): Clamp a 0-100% ✓. Correcto.
- **LTR390** (`sensor_ltr390.c:115,126`): Raw ALS/UVS sin conversión a unidades físicas. Valores negativos (-1.0f) usados como sentinel para "not ready" pero **no se validan en el caller** (`mole_openclaw.c:43`).

### 2.5 Graceful Degradation

**Hallazgo INFO-I2C-05:** El LTR390 tiene fallback MOCK correcto:

```c
// main.c:218-222
esp_err_t err_ltr = sensor_ltr390_init(i2c_bus, &ltr390);
if (err_ltr != ESP_OK) { ltr390 = NULL; }

// mole_openclaw.c:42-48
if (mctx->ltr390) { sensor_ltr390_read(...); }
else { uv = 3.5; lux = 8500.0; }
```

**Sin embargo, DHT20 y Soil usan `ESP_ERROR_CHECK()` en `main.c:214-215`, lo que causa `abort()` si el sensor falla.** No hay graceful degradation para estos sensores.

---

## 3. Resiliencia de Red (BLE, WiFi, mDNS, WebSocket)

### 3.1 BLE Provisioning con Seguridad NULA

**Hallazgo CRIT-NET-01:** `main.c:130`:

```c
wifi_prov_mgr_start_provisioning(WIFI_PROV_SECURITY_0, NULL, "Mole_OpenClaw_Node", NULL);
```

`WIFI_PROV_SECURITY_0` = **sin cifrado ni autenticación**. Cualquier dispositivo BLE en rango puede enviar credenciales WiFi al nodo. Un atacante puede provisionar el nodo con credenciales de un AP malicioso, capturando todo el tráfico posterior.

**Impacto:** CRÍTICO — violación directa de ETSI EN 303 645 §5.1 (no credentials in plaintext).

**Recomendación:** Migrar a `WIFI_PROV_SECURITY_1` (Curve25519 + AES-CTR) o `WIFI_PROV_SECURITY_2` (SRP6a). sdkconfig ya habilita `CONFIG_ESP_PROTOCOMM_SUPPORT_SECURITY_VERSION_1=y` y `_VERSION_2=y` (L1701-1703).

### 3.2 Reconexión WiFi sin Backoff Exponencial

**Hallazgo WARN-NET-02:** `main.c:84-89`:

```c
} else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
    vTaskDelay(pdMS_TO_TICKS(2000));  // Fixed 2s delay
    esp_wifi_connect();
```

Delay fijo de 2 segundos. En caso de AP caído, el ESP32 intentará reconexión agresiva cada 2s indefinidamente, consumiendo energía y saturando el canal RF.

**Recomendación:** Implementar exponential backoff (2s → 4s → 8s → ... → 60s max) con jitter.

### 3.3 Bloqueo Indefinido en `xEventGroupWaitBits`

**Hallazgo CRIT-NET-03:** `main.c:133` y `main.c:142`:

```c
xEventGroupWaitBits(wifi_event_group, WIFI_PROV_DONE_EVENT, false, true, portMAX_DELAY);
// ...
xEventGroupWaitBits(wifi_event_group, WIFI_CONNECTED_EVENT, false, true, portMAX_DELAY);
```

`portMAX_DELAY` = bloqueo indefinido. Si el provisioning BLE nunca completa (usuario abandona la app), o si el AP nunca responde, **`app_main` se bloquea permanentemente**. El nodo queda en estado zombie sin watchdog ni recovery.

**Recomendación:** Usar timeout finito (e.g., 5 minutos) + fallback a deep sleep con `MOLE_DEEP_SLEEP_US`.

### 3.4 WebSocket — Sin Manejo de Desconexión

**Hallazgo CRIT-NET-04:** La conexión WebSocket se establece en `mole_openclaw.c:107-113`:

```c
esp_openclaw_node_connect_request_t req = {
    .source      = ESP_OPENCLAW_NODE_CONNECT_SOURCE_NO_AUTH,
    .gateway_uri = CONFIG_MOLE_GATEWAY_URI,
};
ESP_ERROR_CHECK(esp_openclaw_node_request_connect(s_node, &req));
```

- `ESP_ERROR_CHECK` causará `abort()` si la conexión inicial falla.
- No hay handler de eventos WebSocket para reconexión.
- `telemetry_task` (L63-73) solo verifica `s_node != NULL` pero no verifica estado de la conexión WS.
- `ESP_OPENCLAW_NODE_CONNECT_SOURCE_NO_AUTH` = sin autenticación en el handshake.

**Si el servidor OpenClaw Gateway se cae después de la conexión inicial, no hay mecanismo de reconexión visible en el código del usuario.** La reconexión dependería enteramente de la implementación interna de `esp-openclaw-node v1.0.0`.

### 3.5 Ausencia de mDNS

**Hallazgo WARN-NET-05:** El contexto del proyecto menciona resolución por mDNS del Gateway OpenClaw, pero el código usa una **IP hardcodeada en Kconfig**:

```
CONFIG_MOLE_GATEWAY_URI="ws://192.168.1.100:18789/ws"   # sdkconfig:376
```

No hay `#include "mdns.h"` ni llamadas a `mdns_query_ptr()` / `mdns_query_srv()` en ningún archivo fuente. El Gateway se resuelve estáticamente.

### 3.6 NTP Timeout No Fatal

**Hallazgo INFO-NET-06:** `main.c:182`:

```c
mole_ntp_wait_sync(10000);  // Block up to 10s
```

`mole_ntp_wait_sync` retorna `ESP_ERR_TIMEOUT` si NTP no sincroniza en 10s, pero **el retorno no se verifica con `ESP_ERROR_CHECK`**. El firmware continúa sin reloj válido. La protección está en `handle_sensor_read()` (`mole_openclaw.c:26-29`) que rechaza lecturas si `!mole_ntp_is_synced()`. Esto es aceptable como degradación elegante.

---

## 4. Seguridad y Particionado

### 4.1 IP Hardcodeada en Kconfig

**Hallazgo CRIT-SEC-01:** `Kconfig.projbuild:5`:

```
default "ws://192.168.1.100:18789/ws"
```

Confirmado en sdkconfig compilado (L376). No es un secreto per se, pero vincula el firmware a una topología de red específica. Sin mDNS, cualquier cambio de IP del gateway requiere recompilación.

### 4.2 NVS Encryption — Configuración Incompleta

**Hallazgo CRIT-SEC-02:** La cadena de seguridad de NVS está **rota**:

1. `sdkconfig.defaults:12` → `CONFIG_NVS_ENCRYPTION=y` ✓
2. `partitions.csv:6` → `nvs, data, nvs, 0x9000, 0x6000, encrypted` ✓
3. `partitions.csv:9` → `nvs_keys, data, nvs_keys, 0x1F0000, 0x1000` ✓
4. **PERO** `sdkconfig:302` → `# CONFIG_SECURE_BOOT is not set` ✗
5. **PERO** `sdkconfig:1955` → `# CONFIG_FLASH_ENCRYPTION_ENABLED is not set` ✗

**Sin Flash Encryption habilitado, la partición `nvs_keys` almacena las claves de cifrado NVS en texto plano en la flash.** Un atacante con acceso físico al ESP32 puede leer la flash via UART/JTAG, extraer las claves NVS del sector `0x1F0000`, y descifrar la partición NVS para obtener la **clave privada Ed25519**.

**Impacto:** CRÍTICO — el modelo Zero-Trust queda completamente comprometido sin Flash Encryption + Secure Boot.

### 4.3 Clave Privada Ed25519 — Scrubbing Insuficiente

**Hallazgo CRIT-SEC-03:** `mole_identity.c:161`:

```c
memset(priv_buf, 0, sizeof(priv_buf));
```

El compilador puede optimizar este `memset` ya que `priv_buf` no se usa después. En C, un `memset` seguido de fin de scope es **Dead Store** y puede ser eliminado por GCC con `-O2` o superior.

**Recomendación:** Usar `mbedtls_platform_zeroize(priv_buf, sizeof(priv_buf))` que es resistente a optimización del compilador. Actualmente `CONFIG_COMPILER_OPTIMIZATION_DEBUG=y` (sdkconfig:389) lo protege, pero en producción con `-Os` será vulnerable.

### 4.4 Clave Privada en Contexto mbedTLS Persistente

**Hallazgo CRIT-SEC-04:** Después de generar la clave y guardarla en NVS, el contexto `id->pk` (que contiene `mbedtls_ecp_keypair` con la clave privada `d`) **permanece en RAM durante toda la vida del dispositivo** (`mole_identity.c:172`, `id->initialized = true`).

La clave privada vive en heap accesible. Un exploit de buffer overflow en cualquier otro componente podría leer esta memoria.

**Recomendación:** Después de guardar en NVS, limpiar el componente privado: `mbedtls_mpi_free(&ec->MBEDTLS_PRIVATE(d))`. Recargar desde NVS solo cuando se necesite firmar.

### 4.5 DRBG Personalization String Débil

**Hallazgo WARN-SEC-05:** `mole_identity.c:93`:

```c
mbedtls_ctr_drbg_seed(&id->drbg, mbedtls_entropy_func, &id->entropy,
                       (const unsigned char *)"mole_id", 7);
```

El string de personalización `"mole_id"` es idéntico en todos los dispositivos. Esto no compromete la seguridad (la entropía viene del hardware RNG), pero viola la recomendación NIST SP 800-90A §8.7.2 de usar personalización única por instancia.

### 4.6 Curve25519 ≠ Ed25519

**Hallazgo WARN-SEC-06:** El código genera una clave `MBEDTLS_ECP_DP_CURVE25519` (ECDH, Montgomery curve) en `mole_identity.c:119`, pero la documentación, headers, y constantes (`MOLE_ED25519_*`) refieren a **Ed25519** (EdDSA, Edwards curve). Curve25519 es para Diffie-Hellman, no para firmas. `mbedtls_pk_sign()` con Curve25519 probablemente fallará o producirá firmas inválidas.

**Recomendación:** La dependencia `espressif/libsodium v1.0.21` (en `dependencies.lock`) proporciona `crypto_sign_ed25519_*()` nativo. Migrar a libsodium para Ed25519 real.

---

## 5. Plan de Refactorización Bare-Metal — Checklist Priorizado

### Prioridad P0 — Seguridad (Bloquea despliegue)

| # | Archivo | Línea | Acción |
|---|---|---|---|
| 1 | `main.c` | L130 | Cambiar `WIFI_PROV_SECURITY_0` → `WIFI_PROV_SECURITY_1` con proof-of-possession |
| 2 | `sdkconfig.defaults` | NUEVO | Agregar `CONFIG_SECURE_FLASH_ENC_ENABLED=y` y `CONFIG_SECURE_BOOT=y` |
| 3 | `mole_identity.c` | L161 | Reemplazar `memset()` → `mbedtls_platform_zeroize()` |
| 4 | `mole_identity.c` | L119 | Cambiar `MBEDTLS_ECP_DP_CURVE25519` → libsodium `crypto_sign_ed25519_keypair()` |
| 5 | `mole_identity.c` | L172 | Post-save, limpiar clave privada del contexto pk en RAM |
| 6 | `mole_openclaw.c` | L108 | Cambiar `ESP_OPENCLAW_NODE_CONNECT_SOURCE_NO_AUTH` → autenticación con firma Ed25519 |

### Prioridad P1 — Estabilidad (Causa crashes/hangs)

| # | Archivo | Línea | Acción |
|---|---|---|---|
| 7 | `sensor_ltr390.c` | L20 | Corregir `LTR390_ADDR` de `0x1C` → `0x53` (per datasheet) |
| 8 | `main.c` | L133,142 | Reemplazar `portMAX_DELAY` → timeout finito + fallback deep sleep |
| 9 | `main.c` | L214-215 | Envolver `sensor_dht20_init`/`sensor_soil_init` en fallback con MOCK (como LTR390) |
| 10 | `mole_openclaw.c` | L113 | Reemplazar `ESP_ERROR_CHECK` → manejo graceful con reintentos |
| 11 | `main.c` | L84-89 | Implementar exponential backoff en reconnect WiFi |
| 12 | `mole_openclaw.c` | L115 | Aumentar stack `telemetry_task` 4096 → 6144 |

### Prioridad P2 — Robustez (Degradación en campo)

| # | Archivo | Línea | Acción |
|---|---|---|---|
| 13 | `sensor_dht20.c` | L76 | Agregar retry loop (3 intentos) en `i2c_master_transmit` |
| 14 | `sensor_ltr390.c` | L53,59 | Agregar retry loop + verificar return values de `read_reg`/`write_reg` |
| 15 | `sensor_dht20.c` | L109-110 | Agregar validación de rango: T ∈ [-40, 80], H ∈ [0, 100] |
| 16 | `mole_openclaw.c` | L40-50 | Agregar `SemaphoreHandle_t` para serializar acceso I2C |
| 17 | `Kconfig.projbuild` | L3-8 | Eliminar default IP. Implementar mDNS discovery (`_openclaw._tcp`) |
| 18 | `sdkconfig.defaults` | NUEVO | Agregar `CONFIG_FREERTOS_WATCHPOINT_END_OF_STACK=y` |

### Prioridad P3 — Deuda Técnica

| # | Archivo | Línea | Acción |
|---|---|---|---|
| 19 | `mole_identity.c` | N/A | Crear `mole_identity_deinit()` con `mbedtls_pk_free`, `_entropy_free`, `_ctr_drbg_free` |
| 20 | `mole_openclaw.c` | L56 | Documentar contrato de ownership de `*out_payload_json` (quién hace `free()`) |
| 21 | `mole_openclaw.c` | L63-73 | Implementar emisión real de telemetría (actualmente solo `ESP_LOGI`) |
| 22 | `sensor_ltr390.c` | L115,126 | Convertir raw counts → lux y UV Index con fórmulas del datasheet |
| 23 | `mole_config.h` | L34 | Eliminar `MOLE_LTR390_ADDR` sin uso o usarlo en el driver |
| 24 | `mole_identity.c` | L93 | Personalizar DRBG seed con chip MAC: `esp_efuse_mac_get_default()` |
| 25 | `mole_ntp.c` | L22 | Cambiar `volatile bool` → `_Atomic bool` o proteger con mutex |

---

## Resumen Ejecutivo

| Categoría | Críticos | Altos | Medios | Bajos |
|---|---|---|---|---|
| Memoria/FreeRTOS | 1 | 1 | 1 | 0 |
| I2C/Sensores | 1 | 0 | 2 | 1 |
| Red/Conectividad | 2 | 0 | 1 | 1 |
| Seguridad/Crypto | 4 | 0 | 2 | 0 |
| **Total** | **8** | **1** | **6** | **2** |

**Veredicto:** El firmware **NO está listo para despliegue en producción**. Los hallazgos CRIT-SEC-02 (NVS sin Flash Encryption), CRIT-NET-01 (BLE sin autenticación), y CRIT-SEC-06 (Curve25519 vs Ed25519) representan vulnerabilidades fundamentales que invalidan el modelo Zero-Trust declarado. Se recomienda abordar los 6 items P0 antes de cualquier piloto en campo.
