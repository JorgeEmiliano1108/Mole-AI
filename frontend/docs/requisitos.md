# Requisitos del Frontend — Mole-AI

## 1. Requisitos Funcionales (RF)

### 1.1 Autenticación y Sesión

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-01 | Login con JWT | Inicio de sesión con username + password. Backend retorna JWT. | Alta | ✅ Cumple | `login.html`, `ApiService.js` |
| RF-02 | Registro de usuario | Formulario de registro con username, email, password, confirmación. | Alta | ✅ Cumple | `login.html` |
| RF-03 | Cierre de sesión | Limpia JWT de localStorage y ApiService; redirect a /login. | Alta | ✅ Cumple | `ApiService.js`, `sessionManager.js` |
| RF-04 | Refresh automático de JWT | Si token tiene >15 min de edad, se refresca vía `auth/refresh/`. | Alta | ✅ Cumple | `sessionManager.js` |
| RF-05 | Logout por inactividad | Si no hay actividad del usuario por >20 min, se cierra sesión automáticamente. | Media | ✅ Cumple | `sessionManager.js` |
| RF-06 | Guardia de ruta | Páginas protegidas redirigen a /login si no hay token. | Alta | ✅ Cumple | `main.js:78` |
| RF-07 | Recuperación de contraseña | Formulario "Olvidé mi contraseña" vía API. | Media | ✅ Cumple | `login.html` |

### 1.2 Dashboard IoT

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-08 | KPIs de sensores en tiempo real | Humedad, temperatura, pH, UV con polling cada 30s. | Alta | ✅ Cumple | `health.js`, `dashboard.html` |
| RF-09 | Vista dual Botánico/SRE | Bot toggle entre vista de operador (botánico) y administrador (SRE). | Media | ✅ Cumple | `health.js` |
| RF-10 | Registro de plantas | Modal para agregar nueva planta con nombre y especie. | Alta | ✅ Cumple | `crops.js`, `health.js` |
| RF-11 | Health status por dispositivo | Indicador de salud del nodo ESP32 con datos de sensores. | Alta | ✅ Cumple | `health.js` |
| RF-12 | Gráfica de historial | Línea de tiempo con datos históricos de sensores. | Media | ✅ Cumple | `adminDashboard.js` |

### 1.3 Chat IA Multimodal

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-13 | Chat conversacional | Motor de chat basado en LLM (NVIDIA NIM). | Alta | ✅ Cumple | `chat.js` |
| RF-14 | Chat con visión | Subir imagen al chat; el análisis visual se envía al motor de visión. | Alta | ✅ Cumple | `chat.js:249` |
| RF-15 | Chat estadístico | Análisis de sensores y gráficas vía motor estadístico. | Media | ✅ Cumple | `chat.js:229` |
| RF-16 | Historial de chat persistido | Mensajes guardados en localStorage y recargados al abrir el chat. | Media | ✅ Cumple | `chat.js` |
| RF-17 | Nuevo inicio de conversación | Botón para limpiar historial y generar nuevo sessionId. | Media | ✅ Cumple | `chat.js` |
| RF-18 | Typewriter effect | Respuestas del bot renderizadas carácter por carácter. | Baja | ✅ Cumple | `chat.js:58`, `typewriter.ts` |

### 1.4 Diagnóstico por Visión

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-19 | Subir imagen para diagnóstico | Cámara o galería; preview antes de enviar. | Alta | ✅ Cumple | `vision.js` |
| RF-20 | Resultado de diagnóstico | Especie, condición, severidad, pH estimado, confianza. | Alta | ✅ Cumple | `vision.js:61` |
| RF-21 | Integración con chat | Diagnóstico se envía al chat para análisis contextual. | Media | ✅ Cumple | `chat.js:223` |

### 1.5 Mapas y Georreferenciación

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-22 | Mapa Leaflet con tiles CartoDB dark | Mapa interactivo del terreno. | Alta | ✅ Cumple | `map.js` |
| RF-23 | Capa meteorológica | Marcadores con datos de estaciones meteorológicas vía API. | Media | ✅ Cumple | `map.js` |
| RF-24 | Focos de plaga | Hotspots en el mapa con nivel de alerta. | Media | ✅ Cumple | `map.js` |

### 1.6 Wiki Botánica

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-25 | Catálogo de especies | Grilla con imágenes y nombres de especies. | Alta | ✅ Cumple | `wiki.js` |
| RF-26 | Búsqueda de especies | Búsqueda por nombre con sugerencias de historial. | Alta | ✅ Cumple | `wiki.js` |
| RF-27 | Caché local de catálogo | Especies cacheadas en localStorage para consulta offline. | Media | ✅ Cumple | `wiki.js` |

### 1.7 Administración (CMD CENTER)

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-28 | Dashboard de KPIs globales | Tarjetas con métricas: plantas activas, alerts, uptime, nodos. | Alta | ✅ Cumple | `admin.js` |
| RF-29 | Flota IoT | Grid de nodos ESP32 con health radar chart. | Alta | ✅ Cumple | `admin.js` |
| RF-30 | MLOps | Curvas de entrenamiento, tabla de versiones de modelo. | Media | ✅ Cumple | `admin.js` |
| RF-31 | Centro de alertas | Lista de alertas críticas/warning/info con acknowledge y delete. | Media | ✅ Cumple | `admin.js` |
| RF-32 | Exportar datos | Descarga de reporte TXT con datos del dashboard. | Baja | ✅ Cumple | `adminDashboard.js` |

### 1.8 IoT y Provisioning

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-33 | Escaneo Bluetooth BLE | Escaneo de dispositivos BLE cercanos (ESP32). | Alta | ✅ Cumple | `services/iot.js` |
| RF-34 | Provisioning WiFi | Ingreso de SSID y password para el nodo ESP32. | Alta | ✅ Cumple | `services/iot.js` |
| RF-35 | Hardware bindings | CRUD de bindings (relación dispositivo ↔ cultivo). | Alta | ✅ Cumple | `bindings.js` |

### 1.9 Privacidad y Cumplimiento

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-36 | Aviso de privacidad LFPDPPP | Banner informativo al primer acceso con botón de aceptar. | Alta | ✅ Cumple | `privacy.js` |
| RF-37 | Consentimiento persistente | Consentimiento guardado en localStorage. | Alta | ✅ Cumple | `privacy.js` |

---

## 2. Requisitos No Funcionales (RNF)

### 2.1 Rendimiento

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-01 | Timeout LLM | Tiempo máximo de espera para respuestas de IA: 120s. | Alta | ✅ Cumple | `ApiService.js:8` |
| RNF-02 | Timeout estándar | Timeout para requests normales: 30s. | Alta | ✅ Cumple | `ApiService.js:7` |
| RNF-03 | Polling intervalo | Polling de health sensors cada 30s. | Alta | ✅ Cumple | `health.js:69` |
| RNF-04 | Chunk splitting | leaflet y echarts en chunks separados vía manualChunks. Leaflet + jsPDF con lazy import (solo dashboard/mapa). Chart.js vía dynamic import (no en manualChunks). | Media | ✅ Cumple | `vite.config.js:19` |
| RNF-05 | Bundle size target | JS total < 500KB gzip. | Media | ✅ Cumple | Chunk principal 102 KB (−84%). Leaflet 148 KB separado. Verificado por `scripts/check-bundle.sh` |
| RNF-06 | Cacheo de assets | Assets inmutables con Cache-Control "public, immutable" 1 año. | Alta | ✅ Cumple | `nginx.conf` |
| RNF-07 | HTML no cacheable | .html con Cache-Control "no-cache, no-store, must-revalidate". | Alta | ✅ Cumple | `nginx.conf` |

### 2.2 Seguridad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-08 | JWT en localStorage | Token almacenado en localStorage (vulnerable a XSS). **Requiere migración a HttpOnly cookie.** | Crítica | ❌ No cumple | FE-DT01 (bloqueado backend) |
| RNF-09 | Anti-XSS render | Cero innerHTML con datos dinámicos. DOMPurify wrapper para HTML controlado. | Crítica | ✅ **Cumple** | 0 innerHTML en `src/js/modules/`. `dom.js:safeHTML()` |
| RNF-10 | CSP header | Content-Security-Policy en respuestas Nginx: `script-src 'self'`. | Alta | ✅ **Cumple** | `nginx.conf:40` |
| RNF-11 | HSTS | Strict-Transport-Security header para HTTPS. | Alta | ❌ No cumple | No implementado (requiere dominio prod) |
| RNF-12 | server_tokens off | No revelar versión de Nginx. | Media | ✅ **Cumple** | `nginx.conf:30` |
| RNF-13 | X-Content-Type-Options | Header: nosniff. | Alta | ✅ Cumple | `nginx.conf` |
| RNF-14 | X-Frame-Options | Header: DENY. | Alta | ✅ Cumple | `nginx.conf` |
| RNF-15 | Auth header en logs | No loguear Authorization header en access log. | Media | ✅ **Cumple** | `nginx.conf` |
| RNF-16 | JWT refresh | Refresh automático de token < 15 min de edad. | Alta | ✅ Cumple | `sessionManager.js` |
| RNF-17 | CORS restringido | Solo orígenes permitidos (localhost, 127.0.0.1, mole-ia.com, mole-ia.duckdns.org). | Alta | ✅ Cumple | `nginx.conf:52` |

### 2.3 Resiliencia

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-18 | Retry exponencial | 3 reintentos con backoff 1s→2s→4s para errores de red/server. | Alta | ✅ Cumple | `ApiService.js:9-10` |
| RNF-19 | Timeout por AbortController | Cada request tiene AbortController con timeout. | Alta | ✅ Cumple | `ApiService.js:312-313` |
| RNF-20 | Mensajes de error amigables | Errores HTTP mapeados a español: 401→sesión expirada, 429→demasiadas solicitudes, etc. | Alta | ✅ Cumple | `ApiService.js:208` |
| RNF-21 | Fallback offline | Catálogo de especies en MoleState (memoria) con lazy load. Historial de búsqueda en localStorage. | Media | ✅ Cumple | `wiki.js` |
| RNF-22 | Sesión guard contra BFCache | Recarga de página no debe mantener sesión zombie. | Media | ✅ Cumple | `main.js:78` |

### 2.4 Mantenibilidad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-23 | Módulos ES6 | Código organizado en módulos ES6 con imports/exports. | Alta | ✅ Cumple | `src/js/modules/` |
| RNF-24 | Dead code zero | Sin archivos JS no referenciados en producción. | Media | ✅ **Cumple** | Solo `ApiService.js` conservado. FE-DT03 ✅ |
| RNF-25 | Tests automatizados | 30 tests de seguridad (Vitest + jsdom). | Media | ✅ **Cumple** | `src/js/modules/__tests__/`. FE-DT15 ✅ |
| RNF-26 | Versiones de dependencias fijas | package.json con versiones exactas o caret; lockfile presente. | Media | ✅ Cumple | `pnpm-lock.yaml` |
| RNF-27 | Zero os.getenv | Sin variables de entorno en frontend (config en AppConfig). | Baja | ✅ Cumple | `config.js` |

### 2.5 Accesibilidad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-28 | Contraste WCAG AA | Relación de contraste ≥ 4.5:1 para texto normal. | Media | ⚠️ Parcial | Pip-Boy OK; Solar no verificado |
| RNF-29 | Navegación por teclado | Todos los modales accesibles vía teclado (Tab, Escape). | Media | ❌ No cumple | Sin focus trap ni skip links |
| RNF-30 | ARIA landmarks | Atributos role y aria-label en regiones principales. | Media | ❌ No cumple | Sin implementar |

### 2.6 Docker y Despliegue

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-31 | Docker multi-stage | Build separado del runtime; imagen final mínima. | Alta | ✅ Cumple | `Dockerfile` |
| RNF-32 | Usuario no-root | Nginx no debe correr como root. | Alta | ✅ **Cumple** | `Dockerfile:45` — `USER nginx` |
| RNF-33 | HEALTHCHECK | Healthcheck en Dockerfile. | Media | ✅ **Cumple** | `Dockerfile:49` — wget cada 30s |
| RNF-34 | Read-only rootfs | Contenedor con `--read-only` + `--tmpfs` | Media | ❌ No cumple | `docs/docker-hardening.md` no existe |
| RNF-35 | Capabilities mínimas | `--cap-drop=ALL --cap-add=NET_BIND_SERVICE` | Media | ❌ No cumple | `docs/docker-hardening.md` no existe |

---

## 3. Deuda Técnica

| ID | Deuda | Impacto | Prioridad | Archivo(s) | Estado |
|----|-------|---------|-----------|------------|--------|
| FE-DT01 | JWT en localStorage | **Crítico** — XSS → token compromise | Alta | `config.js`, `ApiService.js`, `sessionManager.js` | ❌ Abierto (bloqueado backend) |
| FE-DT02 | innerHTML masivo (36→0 usos) | **Crítico** — XSS eliminado | Alta | 9 archivos remediados | ✅ **RESUELTO** |
| FE-DT03 | 17 archivos JS legacy eliminados | **Alto** — peso muerto eliminado | Alta | `static/js/` (solo apiService.js) | ✅ **RESUELTO** |
| FE-DT04 | static/ como publicDir y copia Docker | **Alto** — duplicación, confusión de roles | Alta | `vite.config.js`, `Dockerfile`, `nginx.conf` | ✅ **RESUELTO** |
| FE-DT05 | Chat history limpia al logout | **Alto** — PII residual solucionado | Alta | `sessionManager.js:57` | ✅ **RESUELTO** |
| FE-DT06 | CDN migrados a pnpm (0 CDN scripts) | **Medio** — versiones consistentes | Media | `package.json`, `admin.html`, `dashboard.html` | ✅ **RESUELTO** |
| FE-DT07 | ECharts en package.json + bundle | **Medio** — trackeado | Media | `package.json`, `admin.js` | ✅ **RESUELTO** |
| FE-DT08 | auth/refresh/ endpoint no verificado | **Medio** — puede fallar silenciosamente | Media | `sessionManager.js` | ❌ Abierto (backend) |
| FE-DT09 | CSP header implementado | **Medio** — scripts externos bloqueados | Alta | `nginx.conf:40` | ✅ **RESUELTO** |
| FE-DT10 | server_tokens off | **Medio** — info leakage corregido | Media | `nginx.conf:30` | ✅ **RESUELTO** |
| FE-DT11 | USER nginx en Docker | **Medio** — escalación prevenida | Alta | `Dockerfile:45` | ✅ **RESUELTO** |
| FE-DT12 | TailwindCSS duplicado | **Bajo** — mantenimiento extra | Baja | `src/css/main.css`, `public/css/styles.css` | ✅ **RESUELTO** |
| FE-DT13 | Auth header quitado del log format | **Bajo** — tokens no expuestos | Media | `nginx.conf` | ✅ **RESUELTO** |
| FE-DT14 | `window.*` globals eliminados (18 en F1+F2, 8 bridges en F3) | **Bajo** — migración ES6: navegación, API/UI, auth helpers | Alta | `main.js`, 14 módulos | ✅ **RESUELTO** |
| FE-DT15 | 30 tests de seguridad (Vitest + jsdom) | **Bajo** — red de seguridad | Media | `src/js/modules/__tests__/` | ✅ **RESUELTO** |
| FE-DT16 | Wrapper apiService transicional creado (reemplazó `static/js/apiService.js` legacy). Posteriormente eliminado en FE-DT14 — imports migrados directo a `ApiService.js`. `dashboard-sre.js` y `chatWidget.js` migrados a ES6 modules | **Medio** | `src/js/modules/api/ApiService.js`, `src/js/modules/dashboard/sre.js`, `src/js/modules/ui/chatWidget.js` | ✅ **RESUELTO** |
| FE-DT17 | 4 globals intencionales documentados (MoleState, monitorInterval, socketInstance, logPlantIssue) | **Bajo** — deuda técnica documentada en source | Baja | `main.js`, `memory.js`, `reports.js` | ✅ **RESUELTO** |

---

## 4. Bugs Identificados

| ID | Bug | Severidad | Archivo | Causa Raíz | Estado |
|----|-----|-----------|---------|-----------|--------|
| BUG-01 | `vision/analyze/` endpoint en chat.js usa `upload()` que construye URL duplicada | **Media** | `chat.js:274` | `ApiService.upload()` usa `request()` que normaliza endpoint, pero `_buildUrl()` puede duplicar `/api/v1/` si endpoint ya incluye base | ❌ Abierto |
| BUG-02 | `role` event detail vs localStorage race condition | **Media** | `health.js:79` | `userRoleReady` event puede dispararse antes de que localStorage tenga el rol; fallback a null | ❌ Abierto |
| BUG-03 | sessionManager.js no verifica que auth/refresh/ endpoint exista | **Media** | `sessionManager.js:73` | Si backend no implementa refresh, falla silenciosamente | ❌ Abierto |

---

## 5. Cumplimiento Normativo

| Norma | Estado | Evidencia | Brecha |
|-------|--------|-----------|--------|
| **LFPDPPP** (Ley Federal de Protección de Datos Personales) | ⚠️ Parcial | Banner de privacidad con consentimiento (`privacy.js`). Chat history en localStorage contiene PII sin limpiar al logout | FE-DT05 |
| **OWASP A03 — XSS** | ✅ **Cumple** | 0 innerHTML en src/js/modules/; DOMPurify wrapper. JWT localStorage sigue como riesgo residual (bloqueado backend) | FE-DT01 (parcial) |
| **OWASP A05 — Security Misconfiguration** | ✅ **Cumple** | CSP header; server_tokens off; USER nginx; HEALTHCHECK | Ninguna |
| **WCAG 2.1 AA** | ❌ No cumple | Sin ARIA landmarks, sin skip links, sin keyboard navigation | RNF-28, RNF-29, RNF-30 |
| **ETSI EN 303 645** | ❌ No cumple | JWT en localStorage (credenciales en texto plano en el cliente) | FE-DT01 |

---

## 6. Stack Tecnológico

| Componente | Versión | Propósito |
|-----------|---------|-----------|
| Vite | 6.4.3 | Build tool y dev server |
| pnpm | 11.1.3 | Package manager (workspace) |
| TailwindCSS | 3.4.19 | Framework CSS utility-first |
| PostCSS | 8.5.15 | Procesador CSS |
| Autoprefixer | ^10.4.16 | Prefixes CSS vendor |
| Vitest | 3.2.6 | Test runner unitario |
| jsdom | 26.1.0 | Entorno DOM para tests |
| Chart.js | 4.5.1 | Gráficas en dashboard admin |
| Leaflet | 1.9.4 | Mapas interactivos |
| ECharts | 5.5.0 | Gráficas avanzadas en admin (vía pnpm) |
| jsPDF | 4.2.1 | Generación de PDFs offline |
| DOMPurify | 3.4.11 | Sanitización HTML (anti-XSS) |
| Node.js | 25.9.0 | Entorno de build |
| Nginx | 1.25 | Servidor HTTP + proxy inverso |

---

## 7. Endpoints de API

### 7.1 core_backend (Django — via Nginx catch-all `/api/v1/`)

| Método | Path | Auth | Propósito |
|--------|------|------|-----------|
| POST | `/api/v1/auth/login/` | No | Inicio de sesión local (username/password → JWT) |
| POST | `/api/v1/auth/register/` | No | Registro de nuevo usuario |
| POST | `/api/v1/auth/refresh/` | JWT | Refresh de token JWT |
| POST | `/api/v1/auth/logout/` | JWT | Cierre de sesión (stateless — el cliente descarta el token) |
| GET | `/api/v1/auth/profile/` | JWT | Perfil del usuario autenticado |
| POST | `/api/v1/auth/validate-token/` | No | Validar token Supabase |
| GET | `/api/v1/health/` | JWT | Health check del backend |
| GET | `/health/` | No | Health check público (lambda) |
| GET | `/api/v1/sensor-data/latest/` | No | Datos mock de sensores (legacy) |
| GET | `/api/v1/telemetry/latest/` | JWT | Últimas lecturas de telemetría |
| POST | `/api/v1/sensors/ingest` | JWT | Ingesta de sensores (Zero-Trust JWT) |
| GET | `/api/v1/devices/<uuid:id>/health/` | API Key | Health de dispositivo IoT |
| GET | `/api/v1/devices/<uuid:id>/bindings/` | API Key | Listar bindings de dispositivo |
| POST | `/api/v1/devices/<uuid:id>/bindings/` | API Key | Crear binding para dispositivo |
| DELETE | `/api/v1/devices/<uuid:id>/bindings/<int:binding_id>/` | API Key | Eliminar binding |
| GET | `/api/v1/plants/species/` | JWT | Catálogo de especies (CRUD) |
| GET | `/api/v1/plants/search/` | No | Búsqueda pública de especies |
| POST | `/api/v1/plants/` | JWT | Crear planta de usuario |
| GET | `/api/v1/map/hotspots/` | JWT | Hotspots de plagas en mapa |
| GET | `/api/v1/weather/current/` | No | Clima actual (OpenWeather proxy) |
| POST | `/api/v1/llm/chat/` | JWT | Chat LLM local |
| POST | `/api/v1/iot/nodes/` | JWT | Crear nodo IoT |
| GET | `/api/v1/ai/performance/` | JWT | Métricas de modelos ML |
| GET | `/api/v1/diagnostics/` | JWT | Historial de diagnósticos |
| GET | `/api/v1/tasks/status/<str:task_id>/` | JWT | Estado de tareas asíncronas |
| GET | `/api/v1/admin/statistics` | Admin | Estadísticas del sistema |
| GET | `/api/v1/admin/live-alerts` | Admin | Alertas en vivo |
| POST | `/api/v1/admin/reports/generate` | Admin | Generar reporte maestro |
| POST | `/api/v1/ai/train/rag/` | Admin | Entrenar modelo RAG |
| POST | `/api/v1/ai/train/vision/` | Admin | Entrenar modelo de visión |

### 7.2 Microservicios (ruteados por Nginx directamente, NO pasan por core_backend)

| Método | Path | Microservicio | Auth | Propósito |
|--------|------|---------------|------|-----------|
| POST | `/api/v1/mole-ai/llm/chat/` | mole_chat | JWT | Chat LLM con RAG/CAG |
| POST | `/api/v1/vision/vision/analyze/` | mole_vision | JWT | Diagnóstico por imagen |
| POST | `/api/v1/reports/reports/generate/` | mole_report | JWT | Generar reporte PDF |
| GET | `/api/v1/reports/reports/{id}/` | mole_report | JWT | Status de reporte |
| GET | `/api/v1/reports/reports/{id}/download/` | mole_report | JWT | Descargar PDF generado |

---

## 8. Arquitectura de Módulos

```
index.html ──→ src/js/index-boot.js ──→ src/js/main.js (entry principal)
                                               │
                     ┌─────────────────────────┼─────────────────────────┬───────────────────┐
                     │                         │                         │                   │
                modules/api/              modules/services/          modules/ui/        modules/dashboard/
                ┌──────────┐             ┌────────────────┐      ┌──────────────┐     ┌────────────────┐
                 │config.js │             │chat.js (LLM)   │      │dom.js (safe) │     │userDashboard   │
                 │ApiService.js│           │vision.js (CNN)  │      │security.js   │     │adminDashboard  │
                 └──────────┘             │map.js (Leaflet) │      │spinner.js    │     │sre.js         │
                                         │health.js (poll) │      │navigation.js │
                modules/auth/            │crops.js (CRUD)  │      │menus.js      │
                ┌──────────────┐         │wiki.js (catálogo)│     │history.js    │
                │sessionManager│         │iot.js (BLE prov) │      │i18n.js       │
                └──────────────┘         │bindings.js       │      │theme.js      │
                                         │reports.js (PDF)  │      │tactical.js   │
                                         │supervisor.js     │      │privacy.js    │
                                         │mlops.js          │      │memory.js     │
                                          └────────────────┘      │iot.js (wizard)│
                                                                   │chatWidget.js  │
                                                                   │cursor.js      │
                                                                  └──────────────┘

apiService (singleton, src/js/modules/api/ApiService.js — import ES6)
    │
    └── fetch() → Nginx reverse proxy → Microservicio
```

Patrón: **ApiService centralizado** → servicios importan `apiService` desde `modules/api/ApiService.js` → cada servicio implementa lógica de negocio (render, estado, eventos) → UI modules manejan presentación.

**iot.js dualidad:** `services/iot.js` = BLE provisioning (GATT UUIDs, scan, WiFi bind); `ui/iot.js` = wizard modal (pasos, ping, modales de usuario). Responsabilidades distintas, ambos orquestados por `main.js`.

**Lazy imports:** `map.js` (Leaflet) se carga con `import()` dinámico vía `navigation.registerLazyLoader()`. `navigation.js` importa `loadWiki` y `initIoTView` directamente de `services/`, eliminando los bridges `window.*` tras FE-DT14.

**Archivos TS convertidos a JS:** `cursor.ts` y `typewriter.ts` se migraron a `.js` (Vite compila TS por defecto, pero sin `tsconfig.json` no hay type-checking).

---

## 9. Flujo de Autenticación

```
1. Usuario ingresa credentials → POST /api/v1/auth/login/
2. Backend retorna { token: "jwt..." }
3. apiService.setToken(token) → localStorage moleia_token + mole_jwt
4. sessionManager.js inicia timer:
   - Cada 60s verifica edad del token
   - Si >15 min: POST /api/v1/auth/refresh/ → actualiza token
   - Si inactividad >20 min: clearToken() → redirect /login
5. Cada request:
   - apiService.getToken() → lee de localStorage
   - buildHeaders() → Authorization: Bearer <token>
   - Si token expirado y ruta pública: proceed anónimo
   - Si token expirado y ruta protegida: clearToken() → redirect /login
```

---

## 10. Decisiones de Arquitectura (ADR)

### ADR-001: ApiService como singleton global

**Contexto:** Necesidad de un cliente HTTP único compartido entre módulos ES6 y scripts legacy.

**Decisión:** `apiService = new ApiService()` exportado como ES6 module. Los módulos importan `{ apiService }` directamente.

**Consecuencia:** Sin acoplamiento global. Consumidores importan explícitamente.

### ADR-002: Migración de CDN a pnpm (2026-06-26)

**Contexto:** Slice 2 del plan de seguridad añadió SRI a 5 CDN scripts con hashes incorrectos (no criptográficos). Slice 5 migró todas las dependencias a pnpm.

**Decisión:** Eliminar todos los scripts CDN de `admin.html` y `dashboard.html`. Migrar chart.js, echarts, leaflet (CSS+JS) y jspdf a `package.json`. CSP `script-src 'self'` como defensa complementaria.

**Consecuencia:** 0 CDN externos cargados desde HTML. jsPDF actualizado de 2.5.1→4.2.1 (corrige 8 vulnerabilidades). ECharts añade ~341 KB gzip al bundle.

**Referencia:** `docs/adr/0002-cdn-to-pnpm-migration.md`

### ADR-003: Vite con 4 HTML entry points

**Contexto:** 4 páginas distintas (landing, login, dashboard, admin) que comparten núcleo pero tienen UIs diferentes.

**Decisión:** Múltiples inputs en `rollupOptions.input`. Cada HTML es entry point independiente.

**Consecuencia:** Cada página carga solo lo que necesita. El build genera HTML+JS separados por página.

### ADR-004: JWT en localStorage (con deuda conocida)

**Contexto:** Simplicidad de implementación vs seguridad.

**Decisión:** Usar localStorage para JWT (no HttpOnly cookies).

**Consecuencia:** Vulnerable a XSS (FE-DT01). Documentado como deuda técnica crítica pendiente de migrar.

### ADR-005: static/ como publicDir de Vite + copia Docker (RESUELTO)

**Contexto:** Migración gradual de assets legacy a Vite.

**Decisión:** `publicDir: 'static'` usaba static/ para assets servidos por Vite. Docker adicionalmente copiaba `static/` completo para legacy.

**Resolución (FE-DT04, 2026-06-29):** `static/` eliminado. Assets movidos a `public/`. `publicDir` cambiado a `'public'`. Nginx ya no sirve `/static/`. CSS duplicado unificado via Vite (FE-DT12).
