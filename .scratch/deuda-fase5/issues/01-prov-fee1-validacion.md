# Issue 01: Validación de provisioning FEE1 (ssid/pass/token requeridos)

Status: ready-for-agent
Sev: P0 · Área: firmware · Fase: A

## Evidencia
- `microservices/esp32_node/main/ble_provisioning.c:178-186` guarda los 4 campos como
  opcionales; `:193-195` JSON inválido solo loguea; `:200-203` LTK + semáforo **fuera** del
  `if(root)`, se ejecutan incluso en fallo; `:210` retorna 0 siempre.
- `:142-143` `nvs_set_blob/commit` sin chequear `esp_err_t`.
- `:194` loguea el `buf` crudo con **password y token en el serial** (fuga de secreto).

## Problema
Provisioning incompleto provoca reboot con NVS a medias (ciclo de provisioning confuso);
el secreto WiFi/token queda en logs seriales.

## Aceptación
- Helper `provision_save_credentials()`: ssid+pass+token no-vacíos obligatorios,
  `interval` opcional clamp 1–120; escribe todo o nada (commit OK como condición).
- Semáforo + LTK **solo** en éxito; retorno `BLE_ATT_ERR_VALUE_NOT_ALLOWED (0x13)`
  en fallo (verificado contra `ble_att.h`: no existe `INVALID_ATTR_VALUE`).
- Nunca loguear el payload (solo longitud).
- `idf.py build` (target esp32) verde, 0 warnings; `make test` 44/44.

## Compliance
Auth/telemetría: sin PII/secretos en logs; NVS solo con credenciales completas.

## Comments
(none)
