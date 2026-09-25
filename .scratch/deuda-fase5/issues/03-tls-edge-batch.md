# Issue 03: TLS real en edge-batch (CN + https)

Status: ready-for-agent
Sev: P0 · Área: firmware+backend · Fase: B

## Evidencia
- `microservices/esp32_node/main/transport_layer.c:85,143`
  `.skip_cert_common_name_check = true` + `TODO: enable cert validation in production`.
- `sdkconfig:377` `CONFIG_MOLE_HTTP_URI="http://107.23.238.115:8000/…"` (texto plano).

## Problema
Viola guardrail: telemetría ESP32 solo con TLS. MITM en ingesta.

## Aceptación
- Backend expone `https` para edge-batch con cert válido; firmware incluye CA y
  `skip_cert_common_name_check=false`; URI por defecto `https`.
- Fallback sin handshake → Fail-Safe + Store&Forward (issue 07), nunca plano.
- Build esp32 verde; test de ingesta TLS en staging.

## Compliance
Guardrail telemetría-TLS (AGENTS.md); IFT-016 sin cambios.

## Comments
(none)
