# Requisitos Funcionales y No Funcionales del Frontend Mole.AI v2.1

## Resumen

Este documento enumera los requisitos funcionales (FR) y no funcionales (NFR) del frontend Mole.AI v2.1, basándose exclusivamente en el código fuente analizado. Se docementa el **estado actual de cumplimiento** y las **discrepancias** entre lo implementado y lo esperado.

---

## 1. Requisitos Funcionales (FR)

### 1.1 FRs INCUMPLIDOS (No existen en el código)

| ID | Requisito | Estado | Evidencia |
|----|----------|--------|----------|
| FR-A1 | Recuperación de contraseña por email | ❌ **FALTANTE** | `mlops.js:100-119` tiene la función pero solo hace `alert()`, no envía email real |
| FR-A2 | Sistema de notificaciones push | ❌ **FALTANTE** | No hay implementación de Service Worker ni FCM |
| FR-A3 | Exportación a PDF de reportes | ❌ **FALTANTE** | `reports.js:206-212` solo exporta a `.txt`, no PDF |
| FR-A4 | Gestión completa de perfil de usuario (editar nombre, email, contraseña) | ❌ **FALTANTE** | Solo existe cierre de sesión (`logout`), no edición de perfil |
| FR-A5 | Eliminación de cuenta de usuario | ❌ **FALTANTE** | `iot.js:113-122` tiene el modal pero no hay endpoint de eliminación |
| FR-A6 | Autenticación de dos factores (2FA) | ❌ **FALTANTE** | No hay implementación de 2FA |
| FR-A7 | Lockout de cuenta por intentos fallidos | ❌ **FALTANTE** | No hay lógica de lockout |

### 1.2 FRs PARCIALMENTE IMPLEMENTADOS

| ID | Requisito | Estado | Evidencia | Gap |
|----|----------|--------|-----------|----------|-----|
| FR-B1 | Inicio de sesión de operadores | ⚠️ PARCIAL | `main.js:254-306` | Bypass hardcodeado para "dev/dev" (línea 264-269). No valida complejidad de contraseña |
| FR-B2 | Registro de nuevos operadores | ⚠️ PARCIAL | `main.js:195-251` | No verifica email real, no envía correo de confirmación |
| FR-B3 | Dashboard con telemetría en tiempo real | ⚠️ PARCIAL | `userDashboard.js:126-180` | Solo usa datos de localStorage. No recibe streaming real |
| FR-B4 | Chat con IA copiloto (MS2) | ⚠️ PARCIAL | `chat.js:61-126` | Envía `question` Y `prompt` duplicados. No maneja streaming de respuesta |
| FR-B5 | Diagnóstico de imagen por IA (MS1) | ⚠️ PARCIAL | `vision.js:13-77` | El modal de cámara NO existe en HTMLs actuales |
| FR-B6 | Búsqueda de flora mexicana | ⚠️ PARCIAL | `main.js:635-877` | UI integrada en index.html como reemplazar de typewriter. No hay pagination |
| FR-B7 | Registro de plantas/cultivos | ⚠️ PARCIAL | `crops.js:86-142` | El modal `add-plant-modal` NO existe en templates |
| FR-B8 | Historial de diagnósticos | ⚠️ PARCIAL | `history.js:1-182` | El modal `history-modal` NO existe en templates |
| FR-B9 | Mapa de geolocalización | ⚠️ PARCIAL | `map.js:1-153` | El modal `map-modal` NO existe en templates. Usa Leaflet pero sin tiles propios |
| FR-B10 | Reportes de anomalías | ⚠️ PARCIAL | `reports.js:22-73` | Envía reportes pero no hay UI de bandeja en dashboard |
| FR-B11 | Sistema de favoritos | ⚠️ PARCIAL | `history.js:129-182` | Funciona pero el botón "[ PDF ]" no genera PDF real |
| FR-B12 | MLOps: entrenamiento RAG | ⚠️ PARCIAL | `mlops.js:26-61` | Endpoint configurado pero no hay feedback de progreso |
| FR-B13 | MLOps: fine-tuning CNN | ⚠️ PARCIAL | `mlops.js:63-98` | Envía ZIP pero no valida formato interno del dataset |
| FR-B14 | Aprovisionamiento IoT (ESP32) | ⚠️ PARCIAL | `iot.js:57-101` | El wizard modal NO existe en templates |

### 1.3 FRs CUMPLIDOS

| ID | Requisito | Estado | Evidencia |
|----|----------|--------|----------|
| FR-C1 | Logout / Cierre de sesión | ✅ CUMPLIDO | `main.js:309-322` |
| FR-C2 | Redesignación (olvidar contraseña) | ✅ CUMPLIDO | `mlops.js:100-119` (aunque solo con alert) |
| FR-C3 | Panel Admin MLOps | ✅ CUMPLIDO | `admin.html` + `mlops.js` |
| FR-C4 | Indicador de conexión WebSocket | ✅ CUMPLIDO | `tactical.js:97-107`, usado en dashboard |
| FR-C5 | Sistema de toast notifications | ✅ CUMPLIDO | `tactical.js:25-83` y `apiService.js:368-403` (duplicado) |

---

## 2. Requisitos No Funcionales (NFR)

### 2.1 NFRs INCUMPLIDOS

| ID | NFR | Estado | Evidencia | Impacto |
|----|-----|--------|-----------|---------|
| NFR-01 | WebSocket para tiempo real | ❌ **NO IMPLEMENTADO** | `tactical.js:115-132` define `bindWebSocket()` PERO NUNCA SE USA | Latencia de 5s en lugar de tiempo real |
| NFR-02 | Diseño responsivo mobile-first | ⚠️ PARCIAL | Breakpoints existen PERO algunos overflows en cards | UX inconsistente en móvil |
| NFR-03 | Accesibilidad WCAG 2.1 AA | ❌ **INCUMPLIDO** | ~15 violations de a11y (ver auditF.md) | No cumple estándares |
| NFR-04 | Tiempo de respuesta <200ms | ❌ **FALLIDO** | `setInterval` nunca se limpian, memory leaks | Degradación progresica |
| NFR-05 | Modo offline-first completo | ⚠️ PARCIAL | Cola de sync existe (`userDashboard.js:20-31`) PERO no hay indicador visual al usuario | Usuario no sabe que está offline |
| NFR-06 | Seguridad XSS/CSRF | ⚠️ PARCIAL | No hay sanitización de inputs antes de renderizar innerHTML en `renderPlantResults`, `nextIotStep` | Potencial XSS |
| NFR-07 | Design System tokens completos | ❌ **INCUMPLIDO** | Colores definidos PERO NO USADOS (~70 hardcoded) | Inconsistencia visual |
| NFR-08 | SEO optimizado | ❌ **FALTANTE** | No hay meta tags canonical, Open Graph, JSON-LD |
| NFR-09 | Internationalización (i18n) completa | ⚠️ PARCIAL | Solo español e inglés en `main.js:59-72`. No usa biblioteca dedicada |
| NFR-10 | Lazy loading de imágenes | ❌ **FALTANTE** | Imágenes cargan inmediatamente |
| NFR-11 | Code splitting / chunks | ❌ **FALTANTE** | Un solo bundle巨大的 de JS |
| NFR-12 | Service Worker para PWA | ❌ **FALTANTE** | No hay manifest ni SW |
| NFR-13 | Lighthouse score >90 | ❌ **FALLIDO** | Por incumplir NFR-01, NFR-04, NFR-10 |

### 2.2 NFRs CUMPLIDOS

| ID | NFR | Estado | Evidencia |
|----|-----|--------|-----------|
| NFR-20 | Dark Mode táctico | ✅ CUMPLIDO | Palette completa en tailwind.config.js |
| NFR-21 | Tipografía monospace | ✅ CUMPLIDO | JetBrains Mono + Inter cargados |
| NFR-22 | Minimalismo visual | ⚠️ PARCIAL | Efectos decorativos innecesarios (scanline, etc.) |
| NFR-23 | Retroalimentación visual | ✅ CUMPLIDO | Spinners, toasts, estados de carga |

---

## 3. Análisis de Gap: FRs vs Código

### 3.1 FRsDEFINIDOS PERO SIN IMPLEMENTACIÓN (Modales faltantes)

El código referencing los siguientes modales en el MAPA de MODULES (`main.js:41-57`) PERO estos **NO EXISTEN** en ningún archivo HTML:

```javascript
const MODULES = {
    // ✅ Existen
    intro: 'intro-screen',           // index.html
    login: 'login-screen',          // login.html
    dashboard: 'main-dashboard',    // dashboard.html
    admin: 'admin-dashboard',      // admin.html

    // ❌ NO EXISTEN en templates
    analysis: 'analysis-modal',     // FALTANTE
    contact: 'contact-modal',      // FALTANTE
    addPlant: 'add-plant-modal',   // FALTANTE
    loading: 'loading-scan-modal', // FALTANTE
    diagnosis: 'diagnosis-result-modal', // FALTANTE
    history: 'history-modal',     // FALTANTE
    map: 'map-modal',           // FALTANTE
    iot: 'iot-wizard-modal',    // FALTANTE
    profile: 'user-profile-modal', // FALTANTE
    delete: 'delete-account-modal' // FALTANTE
};
```

**Impacto**: 10 modales referenciados pero no implementados. Las funciones que los usan silenciosamente fallan o muestran mensajes crípticos.

### 3.2 Endpoints Referenciados pero sin Contrato Definido

| Endpoint Esperado | Uso en Frontend | Backend Existe? |
|------------------|----------------|-----------------|
| `/api/v1/plants/register` | `crops.js:111` | Posible 404 |
| `/api/v1/users/{user}/history` | `history.js:60` | Posible 404 |
| `/api/v1/users/{user}/favorites` | `history.js:61` | Posible 404 |
| `/api/v1/favorites/save` | `history.js:154` | Posible 404 |
| `/api/v1/map/distribution` | `map.js:97` | Posible 404 |
| `/api/v1/reports/users` | `reports.js:49` | Posible 404 |
| `/api/v1/reports/plants` | `reports.js:89` | Posible 404 |

---

## 4. Recomendaciones

### 4.1 Alta Prioridad (Critical)

1. **Implementar los 10 modales faltantes** - Esto es blocking para múltiples FRs
2. **Reemplazar colores hardcoded** - Unificar `#00ffaa` → `mole-cyan`
3. **Corregir contratos JSON** - Estandarizar camelCase (`operator_id` → `operator`)
4. **Integrar WebSocket** - O eliminar la lógica mock y usar polling explícito
5. **Agregar cleanup de intervals** - En logout para evitar memory leaks

### 4.2 Media Prioridad

6. **Implementar aria attributes** - Minimizar accessibility violations
7. **Consolidar toast system** - Eliminar duplicación apiService + tactical
8. **Validar formularios** - Agregar validación de complejidad de contraseña
9. **Sanitizar innerHTML** - Prevenir XSS en funciones que renderizan HTML dinámico
10. **Agregar trailing slashes** - A todos los endpoints fetch

### 4.3 Baja Prioridad

11. **Implementar Service Worker** - Para offline-first real
12. **Agregar PWA manifest**
13. **Exportar a PDF real** - Reemplazar `.txt` con library jsPDF
14. **Implementar email real** - Para recuperación de contraseña
15. **Lazy loading** - Para imágenes del dashboard

---

## 5. Matriz de Trazabilidad

| FR/NFR | Priority | Complejidad | Estado |
|--------|----------|-------------|--------|
| FR-A1 | Media | Baja | FALTANTE |
| FR-A2 | Alta | Alta | FALTANTE |
| FR-A3 | Media | Media | FALTANTE |
| FR-A4 | Media | Media | FALTANTE |
| FR-A5 | Baja | Baja | FALTANTE |
| FR-A6 | Alta | Alta | FALTANTE |
| FR-A7 | Media | Baja | FALTANTE |
| FR-B1 | Alta | Baja | PARCIAL |
| FR-B2 | Alta | Media | PARCIAL |
| FR-B3 | Alta | Alta | PARCIAL |
| FR-B4 | Alta | Alta | PARCIAL |
| FR-B5 | Alta | Media | PARCIAL |
| FR-B6 | Media | Media | PARCIAL |
| NFR-01 | Alta | Alta | NO IMPLEMENTADO |
| NFR-02 | Alta | Media | PARCIAL |
| NFR-03 | Alta | Media | INCUMPLIDO |
| NFR-04 | Alta | Baja | FALLIDO |
| NFR-05 | Media | Media | PARCIAL |
| NFR-06 | Alta | Baja | PARCIAL |
| NFR-07 | Media | Alta | INCUMPLIDO |

---

*Documento generado a partir del análisis de código fuente del frontend Mole.AI v2.1*