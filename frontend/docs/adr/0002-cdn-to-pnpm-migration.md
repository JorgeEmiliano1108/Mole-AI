# ADR-0002: Migración de CDN a pnpm y eliminación de SRI

- **Fecha**: 2026-06-26
- **Contexto**: Slice 2 del plan de seguridad añadió SRI (`integrity`) a 5 scripts CDN en `admin.html` y `dashboard.html`. Los hashes fueron generados incorrectamente (no criptográficos). Slice 5 migró todos esos scripts a pnpm, eliminando los tags CDN de los HTML.

## Decisión

Migrar todas las dependencias前端 de CDN a pnpm:

| Dependencia | Antes (CDN) | Después (pnpm) |
|-------------|-------------|-----------------|
| Chart.js | `cdn.jsdelivr.net/npm/chart.js@4.4.1` | `chart.js` en `package.json`, import dinámico |
| ECharts | `cdn.jsdelivr.net/npm/echarts@5.5.0` | `echarts` en `package.json`, `import * as echarts` |
| Leaflet CSS+JS | `unpkg.com/leaflet@1.9.4` | `leaflet` en `package.json`, `import L` + `import 'leaflet/dist/leaflet.css'` |
| jsPDF | `cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1` | `jspdf` en `package.json`, `import { jsPDF }` |

## Consecuencias

### Positivas
- **Cero CDN scripts en HTML**: Sin ataque por compromise de CDN
- **CSP endurecido**: `script-src 'self'` — el navegador bloquea cualquier script externo
- **Actualización proactiva**: jsPDF 2.5.1 → 4.2.1 corrigió 8 vulnerabilidades (2 críticas, 6 altas)
- **Build reproducible**: Dependencies versionadas en `pnpm-lock.yaml`
- **SRI innecesario**: Al no cargar scripts externos, el SRI pierde relevancia

### Negativas
- **Tamaño de bundle**: ECharts añade ~341 KB gzip al build
- **Chunk grande**: `echarts-Do1v-ePZ.js` (1.03 MB sin comprimir) — supera el límite de 500 KB, genera warning de Vite

### Lecciones aprendidas
- Los hashes SRI deben generarse con `openssl dgst -sha384 -binary | base64`, no inventarse
- La skill `tdd` (test → fail → implement → pass) habría detectado el error en Slice 2
- El test `scripts/test-sri.sh` ahora verifica que cualquier hash SRI futuro sea criptográficamente válido

## Estado

**Aceptada**. Implementada en Slice 5. Los HTML `admin.html` y `dashboard.html` no contienen CDN scripts.

## Referencias

- `scripts/test-sri.sh`: Test de validación de hashes SRI
- `scripts/check-csp.sh`: Validación de CSP (`script-src 'self'`)
- `vite.config.js`: `manualChunks` para chart.js, leaflet, echarts
