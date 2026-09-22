# Spec GATT — Telemetría BLE en vivo (FEE2)

- **Estado:** aceptado con modificación de trama (veredicto arquitectónico
  2026-09-22: punto fijo i16/u16; ventana y MTU aprobados sin cambios)
- **Padre:** `docs/adr/0005-ble-live-telemetry.md` (decisión) · issue `17-ble-live.md`
- **Lenguaje:** `CONTEXT.md` — Telemetría, Trama edge (`edge_frame.h`), Espécimen
- **Cumplimiento:** `enforce-compliance` IFT-016 (radio BLE) + LFPDPPP (cero PII
  por BLE) + Guardrail A (path servidor TLS intacto como fallback permanente)

## 0. Resumen

Se añade al servicio BLE existente `0xFEE0` una characteristic `0xFEE2`
(`READ` + `NOTIFY` + descriptor CCC `0x2902`) que publica la última
Telemetría del nodo en binario compacto little-endian, mirror 1:1 de la
Trama edge (`microservices/esp32_node/main/include/edge_frame.h`).
`0xFEE1` (`WRITE`, provisioning JSON `ssid/pass/token/interval`) queda intacto.
Sin BLE, todo sigue vía servidor (`edge-batch` → HTTP) — fallback permanente.

## 1. UUIDs y GATT

| Elemento | UUID | Propiedades | Seguridad |
|---|---|---|---|
| Servicio primario | `0xFEE0` (16-bit) | — | `SECURITY_1` (heredada) |
| Provisioning (existente) | `0xFEE1` | `WRITE` (sin respuesta, ≤512B JSON) | idem, bonding existente (`ble_provisioning.c`, store LTK en NVS `mole_prov`) |
| **Telemetría live (nueva)** | **`0xFEE2`** | **`READ` + `NOTIFY`** | idem; **el `auth_token` jamás viaja por BLE** |
| CCC de FEE2 | `0x2902` | `READ` + `WRITE` (`0x0000` off / `0x0001` notify on) | idem |

- Nombre de anuncio live: `mole-agri-sensor` (`MOLE_NODE_NAME`, `mole_config.h`).
  Provisioning conserva el legacy `"MoleProvision"` (sin regresión de flota).
- Advertising `ADV_IND` incluye UUID de servicio `0xFEE0` (filtro de scan en app).
- Pairing: Just Works (`sm_io_cap = NO_IO`, ya en `ble_provisioning.c:266`);
  se reutiliza el bond store existente. Sin PII en ningún AD structure.

## 2. Trama binaria FEE2 (little-endian, punto fijo, mirror de `edge_frame_t`)

Veredicto 2026-09-22: **aritmética de punto fijo 16-bit** (los `f32`
fuerzan fragmentación). El ESP32 multiplica ×100 y envía enteros; la app
Flutter divide entre 100. Orden fijo; ambientales condicionales al bitmask
`valid` (bits = `AMBIENT_VALID_*_BIT` de `edge_frame.h:20-24`).

| Offset | Campo | Tipo LE | Escala / rango |
|---|---|---|---|
| 0 | `ts` | `u32` | epoch s (hasta 2106; `edge_frame_t.ts` double se trunca) |
| 4 | `ri` | `u8` | report interval min, clamp 1–120 (`MOLE_REPORT_INTERVAL_DEFAULT 5`) |
| 5 | `valid` | `u8` | bit0=t bit1=h bit2=l bit3=u; `dg = ~valid & 0x0F` |
| 6 | `t` | `i16` | solo si bit0; °C×100 → −4000…8000 (−40…80 °C, DHT20 `0x38`) |
| +2 | `h` | `u16` | solo si bit1; %×100 → 0…10000 (clamp) |
| +2 | `l` | `u16` | solo si bit2; lux directo 0…65535 (LTR390 `0x53`, cabe exacto) |
| +2 | `u` | `u16` | solo si bit3; UVI×100 → 0…1500 (clamp) |
| +0 | `soil_count` | `u8` | 0–8 (`EDGE_FRAME_MAX_SOIL_PINS`); clamp |
| ×N | sonda | **2 B** | `b0 = (ch<<4) \| (adc>>8)`, `b1 = adc & 0xFF`: canal ADC1 `ch` 0–7 (3 bits, vía `MOLE_GPIO_TO_ADC1_CHANNEL`, pines 32–39) + ADC crudo 12-bit 0–4095 (`MOLE_SOIL_AIR_VAL/WATER_VAL`) |

Por qué 2 B por sonda: el ADC del ESP32 es nativamente 12-bit, así que
`ch(3b)+adc(12b)` calza en 16 bits sin pérdida; el mapeo canal→GPIO vive en
ambos lados (`mole_config.h:38-46` ↔ tabla Dart). Pin inválido (fuera de
32–39): la sonda se omite, la trama no falla.

**Tamaños:** mínima útil (1 campo + 1 sonda) `4+1+1+2+1+2 = 11 B`;
**típica completa (4 campos + 2 sondas) `4+1+1+8+1+4 = 19 B ≤ 20 B`** →
cabe en **una notificación MTU-23** (3 B overhead ATT). Máxima
(4 campos + 8 sondas) `31 B` → requiere MTU negociado (§3).

## 3. MTU y fragmentación

1. La trama típica (19 B) cabe en MTU-23 por defecto: **cero negociación
   en el caso común**.
2. La app **solicita MTU ≥ 64** tras conectar (hasta 512) para cubrir la
   trama máxima (31 B).
3. Si `len(trama) > mtu-3` (MTU denegado / radio antigua): fragmentación
   con header de 2 B por trozo: `[seq:u8][total:u8][chunk…]`, `seq`
   0-based, reintento por `READ` del valor completo vigente (el GATT guarda
   siempre la última trama; `READ` retorna el mismo formato con
   `seq/total`). Caso único también usa `seq=0, total=1` (parser uniforme).
4. Parser Dart idéntico en ambos casos: acumular `total` fragmentos por
   `seq`, timeout 5 s, descartar incompletos. División ×100 al presentar.

## 4. Ciclo de vida del radio y energía (directriz Fase 2b)

El radio BLE **nunca queda encendido permanente** (deep-sleep 5 min,
`MOLE_DEEP_SLEEP_US`). Mecanismo primario:

**Ventana estricta al despertar (primario, sin HW adicional):**
1. Wake (timer) → muestreo sensores → trama FEE2 actualizada en GATT.
2. Se enciende advertising `ADV_IND` durante `BLE_ADV_WINDOW_S`
   (nueva macro, default **30 s**, Kconfig) **en paralelo** al ciclo WiFi
   existente (STA → NTP → `edge-batch` → sleep). El advertising **no
   bloquea** la subida servidor.
3. Si un central se conecta y activa CCC: **una notificación** con la trama
   vigente (+ `READ` bajo demanda). No hay notify periódico: 1 muestra =
   1 anuncio por ciclo de wake.
4. Al expirar la ventana o terminar la subida: radio off → deep-sleep.
5. Costo medible: `30 s × I_adv` por ciclo de 5 min → la prueba de campo
   (criterio issue 17) lo cuantifica en mAh antes del merge.

**Botón físico (alternativa documentada, NO requerida MVP):** GPIO0/BOOT
con ext0-wakeup → ventana extendida 120 s (modo campo-cercano). Exige HW,
debounce y wake-stub: queda fuera del firmware inicial; el spec no lo
prohíbe, solo no lo exige.

**Provisioning intacto:** sin credenciales en NVS, el FSM entra a
`FSM_PROVISIONING` como hoy (`state_machine.c:82-97`, `ble_provisioning` +
captive portal, timeout 300 s). FEE2 existe en GATT pero retorna
`BLE_ATT_ERR_UNLIKELY` (vacío) hasta la primera muestra.

**Coexistencia WiFi+BLE:** pines de sonda solo ADC1 (32–39); la ventana BLE
convive con STA porque el tráfico es mínimo (1–2 notificaciones/ciclo).
Si el SoC reporta conflicto de radio, la subida servidor tiene prioridad
y la ventana BLE se acorta al próximo ciclo (fail-safe, nunca bloqueante).

## 5. Contrato app (sin código en esta fase)

- Deps futuras: `flutter_blue_plus` + `permission_handler`;
  manifest `BLUETOOTH_SCAN/CONNECT` (+`ACCESS_FINE_LOCATION` < API31).
- Flujo: scan filtrado por servicio `FEE0` → connect → discover →
  (provisioning una vez: write JSON `FEE1`) → write CCC `0x0001` →
  parse LE §2 (mismo parser uni/multi-fragmento) → badge de origen
  **BLE-live vs servidor** + merge con `GET telemetry/latest/`
  (contrato §4): el historial servidor es autoritativo; el dato BLE solo
  decora la vista en vivo con su badge.
- Sin BLE (permiso denegado / fuera de rango / radio dormido): todo sigue
  vía backend. Fallback permanente, cero pantallas bloqueadas.

## 6. Aceptación (issue 17, para fase de implementación)

- [ ] Tests HW en verde (`microservices/esp32_node/tests/`, patrón
  `test_state_machine.c` + nuevo `test_fee2_frame.c`: encode/decode,
  bitmask, fragmentación, casos borde MTU-23).
- [ ] Prueba de campo: batería medida por ciclo con ventana 30 s.
- [ ] App: subscribe/unsubscribe contra fake adapter + badge de origen.
- [ ] `flutter analyze` 0 issues; SonarQube 0 Blocker en tocados.

## 7. Trazabilidad

- `edge_frame.h` (contrato canónico) · `mole_config.h` (pines, intervalos,
  NVS) · `ble_provisioning.c:34-67` (FEE0/FEE1) y `:266` (NO_IO) ·
  `state_machine.c:82-97` (provisioning) · `mobile-contract.md §4`
  (merge servidor) · ADR-0005 (decisión) · IFT-016 (radio) ·
  LFPDPPP (sin PII por BLE) · NOM-059 (intacto, vía servidor).
