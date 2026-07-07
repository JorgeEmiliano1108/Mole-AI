# Mole-AI Frontend — Documentación Oficial

## 1. Resumen ejecutivo

**Mole-AI Frontend** es una SPA (Single Page Application) de monitoreo agrícola y diagnóstico IoT. Se conecta a 4 microservicios backend (`mole_chat`, `mole_vision`, `mole_report`, `core_backend`) a través de un proxy inverso Nginx.

**Tecnologías principales:**
- Build tool: Vite 6.4.3
- Package manager: pnpm 11.1.3 (workspace)
- CSS: TailwindCSS 3.4.19 + PostCSS 8.5.15
- Librerías: Chart.js 4.5.1, Leaflet 1.9.4, ECharts 5.5.0, jsPDF 4.2.1, DOMPurify 3.4.11
- Tests: Vitest 3.2.6 + jsdom 26.1.0 (30 tests de seguridad)
- Servidor web: Nginx 1.25 (multi-stage Docker)
- Entorno: Node 25.9.0 (build) → Alpine + Nginx (runtime)

**Arquitectura:** 4 HTML entry points (`index.html`, `login.html`, `dashboard.html`, `admin.html`). Módulos ES6 en `src/js/modules/` organizados por capas (api/, services/, ui/, auth/). API service singleton (`apiService` desde `src/js/modules/api/ApiService.js`) con retry exponencial y manejo de JWT, importado como ES6 module.

---

## 2. Requisitos funcionales (RF)

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|------------------------|
| RF-01 | Autenticación | Login/registro con JWT Bearer | Usuario puede registrarse, iniciar sesión, y recibir token JWT. Token se refresca automáticamente si tiene >15 min de edad |
| RF-02 | Chat IA multimodal | Chat con 3 motores: conversacional, visión, estadísticas | Usuario envía texto o imagen; recibe respuesta en formato typewriter con HTML sanitizado |
| RF-03 | Diagnóstico por visión | Subir imagen de planta para diagnóstico CNN | Usuario sube foto; sistema devuelve especie, condición, severidad, pH estimado, confianza |
| RF-04 | Dashboard IoT en tiempo real | Monitoreo de sensores con polling cada 30s | KPIs (humedad, temperatura, pH, UV) se actualizan automáticamente. Vista dual Botánico/SRE |
| RF-05 | Mapa Leaflet con telemetría | Mapa interactivo con capas meteorológicas y focos de plaga | Usuario puede ver estaciones meteorológicas y hotspots en mapa con tiles CartoDB dark |
| RF-06 | Gestión de cultivos | CRUD de plantas con registro de incidencias | Usuario puede agregar, editar, eliminar plantas; registrar diagnósticos y ver historial |
| RF-07 | Wiki botánica táctico | Catálogo de especies con búsqueda y caché local | Usuario busca especies; resultados se cachean en localStorage para modo offline |
| RF-08 | Dashboard Admin (CMD CENTER) | KPIs, flota IoT, entrenamiento MLOps, alertas | Admin ve charts (Chart.js + ECharts5), estado de nodos ESP32, curvas de entrenamiento CNN |
| RF-09 | Provisioning IoT | Escaneo Bluetooth + provisioning WiFi para ESP32 | Usuario escanea dispositivos BLE, ingresa SSID/pass, envía credenciales al nodo |
| RF-10 | Reportes PDF | Generación y descarga de reportes de diagnóstico | Usuario solicita reporte; se genera vía Celery + mole_report; se descarga como PDF |
| RF-11 | Aviso de privacidad LFPDPPP | Banner con consentimiento al primer acceso | Usuario ve banner una vez; al aceptar, el banner no se muestra más |
| RF-12 | Wiki con información de especies | Catálogo táctico de especies con búsqueda y resultados | Usuario busca especies por nombre; resultados se muestran en grilla |
| RF-13 | Soporte multi-idioma | Interfaz traducible, detección automática del navegador | Usuario puede cambiar idioma manualmente o se detecta automáticamente |

---

## 3. Requisitos no funcionales (RNF)

| ID | Nombre | Descripción | Prioridad |
|----|--------|-------------|-----------|
| RNF-01 | Tiempo de respuesta IA | Chat LLM responde en ≤120s (timeout hard) | Alta |
| RNF-02 | Polling sensores | Dashboard IoT se actualiza cada 30s | Alta |
| RNF-03 | Autenticación JWT | Token gestionado con refresh automático (umbral 15 min) | Alta |
| RNF-04 | Anti-XSS | Renderizado safe: usar textContent, no innerHTML con datos dinámicos | Crítica |
| RNF-05 | Sesión persistente | Inactividad >20 min → logout automático con redirect a /login | Alta |
| RNF-06 | Modo offline | Catálogo de especies en caché localStorage | Media |
| RNF-07 | Privacidad LFPDPPP | Banner de consentimiento + no persistencia de PII sensible | Alta |
| RNF-08 | Seguridad HTTP | CSP header, X-Content-Type-Options, X-Frame-Options, server_tokens off | Alta |
| RNF-09 | Tamaño bundle | JS total < 500KB gzip. Chunk splitting: chart.js, leaflet separados | Media |
| RNF-10 | Manejo de errores | Errores HTTP mapeados a mensajes amigables en español. Retry exponencial 3 intentos | Alta |
| RNF-11 | Accesibilidad | Contraste mínimo 4.5:1, atributos ARIA, navegación por teclado en modales | Media |
| RNF-12 | Zero `os.getenv` | Sin llamadas a os.getenv fuera de config.py (backend rule, frontend no aplica) | Baja |

---

## 4. Estructura de directorios

```
frontend/
├── index.html              # Landing page con typewriter
├── login.html              # Autenticación (login + registro)
├── dashboard.html          # Dashboard principal (1248 líneas)
├── admin.html              # CMD CENTER admin panel (651 líneas)
├── package.json            # Dependencias y scripts
├── pnpm-lock.yaml          # Lockfile de dependencias
├── pnpm-workspace.yaml     # Configuración pnpm workspace
├── vite.config.js          # Build: 4 inputs, manualChunks (leaflet, echarts), dynamic imports (chart.js, jsPDF)
├── tailwind.config.js      # Tema Pip-Boy / Solar, colores personalizados, animaciones
├── postcss.config.js       # TailwindCSS + autoprefixer
├── nginx.conf              # Proxy inverso a microservicios (242 líneas)
├── Dockerfile              # Multi-stage: builder (node:22) + runtime (nginx:1.25-alpine)
├── .node-version           # Versión de Node para CI
├── cors_headers.conf       # Headers CORS reutilizables
├── .npmrc                  # ignore-scripts, strict-peer-deps
├── scripts/
│   ├── check-csp.sh        # Valida CSP (CI)
│   ├── test-sri.sh         # Valida hashes SRI (tdd)
│   └── check-bundle.sh     # Detecta chunks >500 KB (CI)
├── docs/
│   ├── adr/
│   │   └── 0002-cdn-to-pnpm-migration.md
│   ├── docker-hardening.md # Runtime flags de seguridad
│   └── requisitos.md       # RF/RNF detallados
├── .gitignore
│
├── src/                    # Código fuente moderno (Vite entry)
│   ├── css/
│   │   ├── main.css        # Tailwind directives + custom properties (167 líneas)
│   │   └── themes/
│   │       └── pip-boy.css # CRT overlay + flicker animation
│   └── js/
   │   ├── main.js         # Entry principal (1258 líneas, 29 imports)
│       ├── index-boot.js   # Bootstrap para landing page
│       ├── admin.js        # Lógica CMD CENTER (485 líneas)
│       ├── auth.js         # Session guard + formularios
│       ├── typewriter.ts   # Efecto typewriter con data-typewriter attribute
│       └── modules/
   │           ├── api/
   │           │   ├── ApiService.js    # Cliente HTTP singleton (retry, JWT, AbortController)
   │           │   └── config.js        # AppConfig + JWT helpers
   │           ├── auth/
   │           │   └── sessionManager.js  # Sesión multi-tab (BroadcastChannel)
   │           ├── dashboard/
   │           │   ├── adminDashboard.js  # Charts y reportes admin
   │           │   └── userDashboard.js   # Dashboard offline-first
│           ├── services/
│           │   ├── chat.js        # Chat multimodal (315 líneas)
│           │   ├── vision.js      # Diagnóstico por imagen
│           │   ├── map.js         # Leaflet + weather layers
│           │   ├── health.js      # Device health polling 30s
│           │   ├── crops.js       # CRUD plantas
│           │   ├── wiki.js        # Catálogo táctico
│           │   ├── iot.js         # BLE provisioning
│           │   ├── bindings.js    # Hardware bindings
│           │   ├── reports.js     # Reportes PDF
│           │   ├── supervisor.js  # Sincronización plant inventory
│           │   └── mlops.js       # RAG + CNN training
│           └── ui/
│               ├── dom.js         # Safe DOM utilities (textContent)
│               ├── security.js    # Chat render anti-XSS
│               ├── spinner.js     # Loading states
│               ├── navigation.js  # Field view switcher
│               ├── menus.js       # Menú dropdown
│               ├── history.js     # Historial/favoritos
│               ├── i18n.js        # Multi-idioma
│               ├── theme.js       # Pip-Boy / Solar toggle
│               ├── tactical.js    # Toast + WebSocket indicator
│               ├── privacy.js     # Banner LFPDPPP
│               ├── cursor.ts      # Blinking cursor
│               ├── memory.js      # Chat listener management
│               └── iot.js         # IoT wizard modals
│           └── __tests__/
│               ├── dom.test.js         # 24 tests: el(), safeHTML, safeRender
│               └── sessionManager.test.js # 6 tests: sessionLogout, inactividad, refresh
│
├── public/                  # Static assets servidos por Vite
│   ├── assets/              # Imágenes de marca (2 PNGs)
│   └── favicon.svg          # Favicon
│
├── dist/                    # Build output de Vite (gitignored)
└── staticfiles/             # Django collectstatic artifact (vacío, gitignored)
```

---

## 5. Flujo de datos

```
CLIENTE (Browser)
  │
  ├── index.html → src/js/main.js (entry module ES6)
   │     └── apiService (singleton en src/js/modules/api/ApiService.js, import ES6)
   │         └── fetch() con AbortController + retry exponencial
   │
   ├── login.html → POST /api/v1/auth/login/
   │     └── JWT → localStorage (moleia_token + mole_jwt)
   │         └── apiService.setToken()
  │
  ├── dashboard.html → src/js/main.js
  │     ├── Chat:     POST /api/v1/mole-ai/llm/chat/        → mole_chat:8002
  │     ├── Vision:   POST /api/v1/vision/vision/analyze/   → mole_vision:8001
  │     ├── Reports:  POST /api/v1/reports/reports/{...}/   → mole_report:8003
  │     ├── Health:   GET  /api/v1/health/                  → core_backend:8000
  │     ├── Plants:   GET/POST /api/v1/plants/{...}/        → core_backend:8000
  │     ├── IoT:      GET/POST /api/v1/iot/{...}/           → core_backend:8000
  │     └── Map:      GET  /api/v1/weather/ + Leaflet tiles → core_backend:8000
  │
  └── admin.html → src/js/admin.js
        ├── KPI:     GET /api/v1/metrics/kpi/               → core_backend:8000
        ├── Fleet:   GET /api/v1/iot/fleet/                 → core_backend:8000
        ├── ML:      GET/POST /api/v1/ml/{...}/             → core_backend:8000
        └── Alerts:  GET/POST /api/v1/alerts/{...}/         → core_backend:8000

NGINX Proxy (nginx.conf)
  ├── /api/v1/              → proxy_pass http://django-backend:8000
  ├── /api/v1/vision/       → proxy_pass http://ms1_vision:8001
  ├── /api/v1/mole-ai/      → proxy_pass http://ms2_chat:8002  (proxy_read_timeout 300s)
  ├── /api/v1/knowledge/    → proxy_pass http://ms2_chat:8002
  ├── /api/v1/reports/      → proxy_pass http://ms3_reports:8003
  ├── /admin/               → proxy_pass http://django-backend:8000
  └── /ws/                  → proxy_pass http://django-backend:8000 (WebSocket upgrade)
```

**Headers de seguridad en Nginx:**
- `Content-Security-Policy: default-src 'self'; script-src 'self'; ...` (sin `unsafe-inline` para scripts)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `server_tokens off`
- Authorization removido del log format

**CORS**: Mapa de orígenes permitidos (localhost, mole-ia.com, mole-ia.duckdns.org).

---

## 6. Cumplimiento normativo

| Norma | Requisito | Estado | Evidencia | Acción |
|-------|-----------|--------|-----------|--------|
| LFPDPPP §9 | Aviso de privacidad visible al primer acceso | ✅ | `privacy.js` banner con consentimiento explícito | Ninguna |
| LFPDPPP §11 | Consentimiento para datos personales | ✅ | Botón "ACEPTAR Y CONTINUAR", persiste en localStorage | Ninguna |
| LFPDPPP §17 | Datos sensibles no compartidos sin consentimiento | ⚠️ | Chat history en localStorage sin cifrar; se limpia al logout | Pendiente JWT cookie |
| OWASP A03 (XSS) | No usar innerHTML con datos dinámicos | ✅ | 0 innerHTML en src/js/modules/. DOMPurify wrapper async | Ninguna |
| OWASP A02 (Broken Auth) | JWT en HttpOnly cookie vs localStorage | ❌ | JWT en localStorage (bloqueado: espera backend HttpOnly) | Pendiente Slice 1A |
| OWASP A05 (Security Misconfig) | CSP header + server_tokens off + USER nginx | ✅ | CSP implementado; server_tokens off; USER nginx | Ninguna |
| WCAG 2.1 AA | Contraste mínimo 4.5:1 | ⚠️ | Tema Pip-Boy OK (~5.5:1); falta verificar Solar | Pendiente |
| WCAG 2.1 AA | Navegación por teclado + ARIA | ❌ | Sin skip links, modales sin foco atrapado, sin landmarks | Pendiente |
| ETSI EN 303 645 | Credenciales no en texto plano | ❌ | JWT en localStorage (FE-DT01) | Pendiente Slice 1A |

---

## 7. Deuda técnica identificada

| ID | Severidad | Descripción | Archivo(s) | Acción correctiva |
|----|-----------|-------------|------------|-------------------|
| FE-DT01 | **Crítica** | JWT en localStorage — vulnerable a XSS. Dos keys redundantes (`moleia_token` + `mole_jwt`) | `config.js`, `ApiService.js`, `sessionManager.js` | ⏳ Bloqueado por backend |
| FE-DT02 | **Crítica** | 36 usos de `innerHTML` → **0** en `src/js/modules/` | 9 archivos remediados | ✅ **RESUELTO** |
| FE-DT03 | **Alta** | 17 archivos JS legacy eliminados (solo apiService.js conservado) | `static/js/` | ✅ **RESUELTO** |
| FE-DT04 | **Alta** | `static/` como publicDir de Vite y copiado aparte en Docker | `vite.config.js`, `Dockerfile`, `nginx.conf` | ✅ **RESUELTO** |
| FE-DT05 | **Alta** | Chat history se limpia al logout (`sessionLogout`) | `sessionManager.js:57` | ✅ **RESUELTO** |
| FE-DT06 | **Media** | Chart.js/ECharts migrados a pnpm. 0 CDN scripts en HTML | `admin.html`, `package.json` | ✅ **RESUELTO** |
| FE-DT07 | **Media** | ECharts 5.5.0 en `package.json` + bundle Vite | `admin.js` | ✅ **RESUELTO** |
| FE-DT08 | **Media** | `auth/refresh/` endpoint no verificado | `sessionManager.js` | ❌ Abierto (backend) |
| FE-DT09 | **Media** | CSP header + `script-src 'self'` implementado | `nginx.conf` | ✅ **RESUELTO** |
| FE-DT10 | **Media** | `server_tokens off` implementado | `nginx.conf` | ✅ **RESUELTO** |
| FE-DT11 | **Media** | `USER nginx` en Dockerfile | `Dockerfile:45` | ✅ **RESUELTO** |
| FE-DT12 | **Baja** | TailwindCSS duplicado: src/css/main.css + public/css/styles.css. Unificado via Vite | `main.css`, 4 HTMLs | ✅ **RESUELTO** |
| FE-DT13 | **Baja** | `$http_authorization` eliminado del log_format | `nginx.conf` | ✅ **RESUELTO** |
| FE-DT14 | **Alta** | `window.*` globals eliminados (18 en F1+F2, 8 bridges en F3) | `main.js`, 14 módulos | ✅ **RESUELTO** |
| FE-DT15 | **Baja** | 30 tests de seguridad (Vitest + jsdom) | `src/js/modules/__tests__/` | ✅ **RESUELTO** |
| FE-DT16 | **Media** | Wrapper apiService transicional creado (reemplazó `static/js/apiService.js` legacy). Posteriormente eliminado en FE-DT14 — imports migrados directo a `ApiService.js`. `dashboard-sre.js` y `chatWidget.js` migrados a ES6 modules | `src/js/modules/api/ApiService.js`, `src/js/modules/dashboard/sre.js`, `src/js/modules/ui/chatWidget.js` | ✅ **RESUELTO** |
| FE-DT17 | **Baja** | Documentar 4 globals intencionales residuales (MoleState, monitorInterval, socketInstance, logPlantIssue) | `main.js`, `memory.js`, `reports.js` | ✅ **RESUELTO** |

---

## 8. Guía de desarrollo local

### Prerrequisitos

- Node.js >= 18 (v25.9.0 recomendada)
- pnpm >= 11.1.3 (instalar con `corepack enable && corepack prepare pnpm@11.1.3 --activate`)

### Instalación

```bash
cd frontend
pnpm install
```

### Desarrollo

```bash
pnpm dev
```

Servidor en `http://localhost:5173`. **Nota:** En desarrollo no hay proxy inverso Nginx — los microservicios deben estar corriendo en `localhost:8000` (core_backend), `:8001` (vision), `:8002` (chat), `:8003` (reports).

### Build producción

```bash
pnpm build
```

Output en `dist/`. Incluye `pnpm audit --audit-level high` pre-build.

### Tests

```bash
pnpm test          # 30 tests de seguridad (Vitest)
pnpm test:watch    # Modo watch
```

### Scripts de validación CI

```bash
bash scripts/check-csp.sh      # Valida CSP: script-src 'self', sin unsafe-inline
bash scripts/test-sri.sh       # Valida hashes SRI reales contra CDNs de referencia
bash scripts/check-bundle.sh   # Detecta chunks >500 KB (allowlist: ECharts)
```

### Preview del build

```bash
pnpm preview
```

### Docker

```bash
docker build -t mole-frontend .
docker run --rm \
  --read-only \
  --tmpfs /tmp:size=64M \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  -p 80:80 mole-frontend
```

Ver `docs/docker-hardening.md` para justificación de flags de seguridad.

### Stack completo (docker compose desde raíz del proyecto)

```bash
docker compose up -d
```

---

## 9. Vertical slices (issues priorizados)

| Issue | Descripción | Archivos impactados | Prioridad | Estado |
|-------|-------------|--------------------|-----------|--------|
| VS-FE01 | Migrar JWT a HttpOnly cookie + refresh endpoint | `ApiService.js`, `config.js`, `sessionManager.js`, backend | **Crítica** | ⏳ Bloqueado backend |
| VS-FE02 | Reemplazar innerHTML → textContent + createElement | 9 archivos remediados | **Crítica** | ✅ **COMPLETADO** |
| VS-FE03 | Eliminar 17 archivos JS legacy no referenciados | `static/js/` (excepto apiService.js) | **Alta** | ✅ **COMPLETADO** |
| VS-FE04 | Seguridad Nginx: CSP + server_tokens + USER nginx | `nginx.conf`, `Dockerfile` | **Alta** | ✅ **COMPLETADO** |
| VS-FE05 | Migrar publicDir de static/ a public/ | `vite.config.js`, mover assets | **Alta** | ✅ **COMPLETADO** |
| VS-FE06 | Unificar Chart.js + ECharts a pnpm, 0 CDN scripts | `admin.html`, `package.json` | **Media** | ✅ **COMPLETADO** |
| VS-FE07 | Sanitizar nginx access log + eliminar cors_headers.conf | `nginx.conf` | **Media** | ✅ **COMPLETADO** |
| VS-FE08 | 30 tests de seguridad (Vitest + jsdom) | `src/js/modules/__tests__/` | **Media** | ✅ **COMPLETADO** |
| VS-FE09 | Limpiar chat history en logout | `sessionManager.js:57` | **Media** | ✅ **COMPLETADO** |
| VS-FE10 | Accesibilidad: ARIA landmarks + keyboard nav | HTMLs + módulos UI | **Media** | ❌ Pendiente |
| VS-FE11 | Unificar TailwindCSS (eliminar public/css/styles.css) | Ambos archivos CSS | **Baja** | ✅ **COMPLETADO** |
| VS-FE12 | CI: scripts check-csp.sh + test-sri.sh + check-bundle.sh | `scripts/` | **Media** | ✅ **COMPLETADO** |
| VS-FE13 | HEALTHCHECK + docker-hardening.md | `Dockerfile`, `docs/` | **Media** | ✅ **COMPLETADO** |
