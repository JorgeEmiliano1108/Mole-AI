# Issue 06: ESP_ERROR_CHECK en rutas runtime → degradado

Status: ready-for-agent
Sev: P1 · Área: firmware · Fase: C

## Evidencia
- `main.c:418` `ESP_ERROR_CHECK(esp_wifi_set_config)` + `:421-426` 5× NVS dentro de
  `captive_post_handler` (contexto HTTPD: fallo NVS/WiFi = abort/reboot, no HTTP 500).
- `sensor_init_all:709` `ESP_ERROR_CHECK(i2c_new_master_bus)`, `:711`
  `ESP_ERROR_CHECK(sensor_dht20_init)`, `:722` `ESP_ERROR_CHECK(adc_oneshot_new_unit)`
  pese al diseño degradado (excepción: LTR390 `:713-717` sí maneja con NULL+MOCK).

## Problema
Error recuperable convertido en panic; contradice el diseño degradado del nodo.

## Aceptación
- Handlers HTTP retornan `HTTPD_400/500` con `httpd_resp_send_err`; init de sensores
  degrada por canal (bitmask `dg`) sin abortar.
- Build esp32 verde 0 warnings; boot en placa desnuda llega a provisioning.

## Compliance
Fail-safe antes que abort (nodo rural sin operador).

## Comments
(none)
