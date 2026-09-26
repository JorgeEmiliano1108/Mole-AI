# Issue 03: TLS real en edge-batch (CN + https)

Status: ready-for-human
Sev: P0 · Área: firmware+backend · Fase: B

## Evidencia
- `microservices/esp32_node/main/transport_layer.c:85,143`
  `.skip_cert_common_name_check = true` + `TODO: enable cert validation in production`.
- `sdkconfig:377` `CONFIG_MOLE_HTTP_URI="http://107.23.238.115:8000/…"` (texto plano).

## Problema
Viola guardrail: telemetría ESP32 solo con TLS. MITM en ingesta.

## Aceptación (as-built, diseño no-ruptura)
- nginx 443 activo con CA lab (`scripts/gen-lab-tls.sh`, idempotente, SAN IP
  configurable); `127.0.0.1:8443:443` en compose; sintaxis `nginx -t` OK.
- Firmware: `lab_ca.pem` embebida (solo cert público versionado),
  `skip_cert_common_name_check=false` en HEAD+POST; en `http` se ignora
  (flujo lab intacto), en `https` sin handshake el perform falla y el FSM
  ya emite `EVT_DISCONNECTED/ERROR` (fail-safe existente, sin fallback a plano).
- URI default intacta (operador la cambia a `https://…:8443/…` por menuconfig).
- Evidencia: `curl --cacert ca.crt --resolve mole-edge.local:8443` →
  `http=502 ssl_verify=0` (handshake válido; 502 por falta de upstream en el test).
- `idf.py build` esp32 verde 0 warnings.

## Compliance
Guardrail telemetría-TLS (AGENTS.md); IFT-016 sin cambios.

## Compliance
Guardrail telemetría-TLS (AGENTS.md); IFT-016 sin cambios.

## Comments
(none)
