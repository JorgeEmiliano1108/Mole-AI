# Mole.AI Frontend Audit Report v2.1

## Resumen Ejecutivo

**Fecha de Auditoría**: 2026-04-24
**Versión del Frontend**: v2.1
**Auditor**: Mole.AI Code Review System
**Alcance**: HTML templates, JavaScript modules, Tailwind configuration, CSS assets

---

## 1. Cumplimiento Normativo y Diseño (UI/UX)

### 1.1 Simetría de Vistas

| Vista | Estado | Observaciones |
|-------|--------|--------------|
| index.html (Intro) | ✅ | Layout simétrico con paneles left/right. Corner brackets decorativos correctos. |
| login.html | ✅ | Formulario centrado, responsivo. Banners legales presentes. |
| dashboard.html | ⚠️ | KPI cards bien distribuidos pero Chat drawer tiene estado inconsistente (translate-x-full inicial). |
| admin.html | ✅ | MLOps panel funcional pero sin scroll en kontenores internos. |

**Hallazgo Crítico**: No existe symetría visual en el Chat drawer del dashboard. El panel de chat comienza oculto (`translate-x-full`) pero el toggle para mobile FAB no está synchronized con el estado inicial. Esto genera una experiencia asimétrica donde en desktop se ve el drawer inicialmente oculto a la derecha pero en mobile el FAB aparece sin correspondencia visual clara.

**Recomendación**: Implementar un estado inicial consistente y sincronizado via CSS media queries o JavaScript de inicialización.

### 1.2 Iconografía

| Archivo | Iconos SVG | Uso Correcto |
|---------|-----------|-------------|
| index.html | 3 | ✅ Inline SVG con stroke correctos |
| dashboard.html | 12 | ✅ Inline SVG consistentes |
| login.html | 0 | ⚠️ Link de retorno sin icono |
| admin.html | 8 | ✅ Iconos MLOps presentes |

**Problema**: Los SVG están hardcodeados como inline en lugar de usar un sistema de iconos unificado (ej. Heroicons o Lucide). Esto incrementa el peso del HTML.

### 1.3 Paleta Dark Mode y Condiciones de Alta Luminosidad

La paleta mole-base está correctamente definida en `tailwind.config.js`:

```
mole-base:    #0B0F19  (✅ Fondo principal)
mole-surface: #111827  (✅ Cards/paneles)
mole-border: #1E293B  (✅ Bordes sutiles)
mole-cyan:   #00E5FF  (✅ Acento primario)
mole-green:  #34D399  (✅ Éxito)
mole-amber: #FBBF24  (⚠️ Advertencia)
mole-red:    #F87171  (❌ Error/crítico)
mole-dim:   #94A3B8  (✅ Texto muted)
```

**CRÍTICO — inconsistencia detectada**:

El diseño система DEFINE los colores correctamente, pero el código JavaScript USA colores hardcodeados que no corresponden:

| Uso Observado | Design Token Esperado | Archivo | Línea |
|-------------|---------------------|--------|-------|
| `text-[#00ffaa]` | `text-mole-cyan` | main.js | 432, 450, 470, 651-663, etc. |
| `bg-[#00ffaa]/30` | `bg-mole-cyan/30` | main.js | 437, 651, etc. |
| `text-[#f97316]` | `text-mole-amber` | chat.js | 37, 103 |
| `#00ffaa` (sin prefijo) | `mole-cyan` | múltiplos | - |

**Conclusión de Diseño**: La paleta está definida PERO NO SE USA consistentemente. Aproximadamente 70+ instancias de colores hardcodeados encontrados que contradicen el Design System.

### 1.4 Placeholders y Botones

- **Placeholders**: Usan correctamente `placeholder-mole-dim/40` en la mayoría de formularios.
- **Botones**: Tienen estados `hover` y `focus` definidos, pero:
  - Faltan `focus:ring` explícitos para accesibilidad.
  - Algunos botones en login.html usan `onclick` inline (línea 42).

### 1.5 Minimalismo y Responsividad

✅ CUMPLIDO PARCIALMENTE:

- Breakpoints implementados: `sm`, `md`, `lg`, `xl`.
- Grid responsivo: `grid-cols-1 lg:grid-cols-2`.
- Mobile FAB presente en dashboard (línea 165).

❌ NO CUMPLIDO:

-scanline overlay es fijo en TODAS las páginas aunque no agrega valor funcional.
- Múltiples estilos inline que podrían externalizarse.

---

## 2. Deuda Técnica Frontend

### 2.1 Clases CSS Huérfanas / Sin Uso

Del análisis de tailwind.config.js, las siguientes clases están definirías PERO no se usan en ningún template:

- `shadow-cyber-hover`: definida pero nunca referenciada directamente (solo via hover en Tailwind)
- `animate-cursor-blink`: definida pero nunca referenciada (typewriter usa animate-pulse manualmente)

### 2.2 Código JS Espagueti

**Ubicación**: `src/js/main.js` — 906 líneas

| Patrón | Problema | Severidad |
|--------|---------|-----------|
| `Object.assign(window, ...)` | Exposición de 20+ módulos a window | 🔴 Alta |
| Funciones de 200+ líneas | `typeContent`, `loadFloraSearch`, `nextIotStep` no están modularizadas | 🔴 Alta |
| setInterval sin cleanup | `updateClock` persiste en logout (línea 416) sin limpieza | 🟠 Media |
| Variables globales | `typeInterval`, `window.monitorInterval` como globals | 🟠 Media |

**Evidencia de Espagueti** (main.js líneas 421-527):

```javascript
function nextIotStep(step) {
    // 100+ líneas de DOM manipulation inline
    // Sin separación de concerns
    // Crea elementos con className hardcoded
}
```

### 2.3 Falta de Modularidad

El código tiene signs de arquitectura modular PERO viola principios:

1. **Acoplamiento alto**: Módulos se exponen a window (línea 879-897):
   ```javascript
   Object.assign(window, userDashboard);
   Object.assign(window, adminDashboard);
   // ... 20 módulos más
   ```

2. **Inyección de dependencias inconsistente**: Algunos módulos usan imports, otros esperan window.X

3. **Duplicación de lógica**:
   - `config.js` y `apiService.js` ambos gestionan tokens
   - `tactical.js` y `apiService.js` ambos tienen `showToast`

### 2.4 Manipulaciones Ineficientes del DOM

| Función | Problema | Impacto |
|--------|----------|---------|
| `renderPlantResults` (main.js:779-876) | Usa `document.createElement` + appendChild en loop | Performance |
| `nextIotStep` | Crea todo el DOM en JS en lugar de templates | Maintenance |
| `typeContent` | Usa innerHTML + appendChild para cursor | Memory leak potencial |

### 2.5 Accesibilidad (a11y) — DEFICIENCIAS CRÍTICAS

| Problema | Archivo |.Elementos | Severidad |
|---------|--------|----------|----------|
| `alt=""` ausente | dashboard.html | `#main-img` con `alt="Planta"` genérico | 🟠 Media |
| No visible focus | todos | Buttons sin `focus:outline` explícito | 🔴 Alta |
| aria-live no configurado | chat | `chat-messages` sin aria-live | 🟠 Media |
| aria-expanded | dashboard | Dropdown de perfil sin aria | 🟠 Media |
| Roles ARIA | index.html | Nav buttons sin `role="button"` | 🟠 Media |
| Keyboard navigation | index.html | Botones "[ENTER]" no funcionales | 🔴 Alta |
| Color-only status | dashboard | WS status solo cambia color | 🔴 Alta |

### 2.6 Memory Leaks

1. **updateClock** (main.js línea 416):
   ```javascript
   setInterval(updateClock, 1000); // Nunca se limpia en logout
   ```

2. **typeInterval** (main.js línea 157):
   ```javascript
   typeInterval = setInterval(...) // cleaning parcial solo en loadFloraSearch
   ```

---

## 3. Contratos Backend / Microservicios

### 3.1 Endpoints Definidos vs Usados

El frontend espera los siguientes endpoints (basado en código):

| Endpoint | Método | Uso en Frontend | Archivo | Status |
|----------|--------|---------------|---------|--------|
| `/api/v1/auth/login/` | POST | ✅ | main.js:282 | ✅ |
| `/api/v1/auth/register/` | POST | ✅ | main.js:234 | ✅ |
| `/api/v1/auth/password-reset/` | POST | ✅ | mlops.js:105 | ✅ |
| `/api/v1/chat/` | POST | ✅ | chat.js:90 | ⚠️ |
| `/api/v1/diagnostic/` | POST/UPLOAD | ✅ | vision.js:46 | ⚠️ |
| `/api/v1/plants/search/` | GET | ✅ | main.js:744 | ⚠️ |
| `/api/v1/plants/register` | POST | ✅ | crops.js:111 | ❌ |
| `/api/v1/users/{user}/plantas` | GET | ✅ | supervisor.js:16 | ⚠️ |
| `/api/v1/ai/rag/train/` | POST | ✅ | mlops.js:41 | ⚠️ |
| `/api/v1/ai/vision/retrain/` | POST | ✅ | mlops.js:78 | ⚠️ |
| `/api/v1/sistema/override` | POST | ✅ | supervisor.js:79 | ⚠️ |
| `/api/v1/api/iot/provisioning` | POST | ✅ | iot.js:72 | ⚠️ |

### 3.2 Discrepancias de Contratos (JSON Keys)

#### chat.js (líneas 90-95):

```javascript
await moleApi.post('chat/', {
    question: query,
    prompt: query,
    engine: engine,
    session_id: localStorage.getItem('moleia_current_user') || 'anon'
});
```

**Problema**: Enviando `question` Y `prompt` con el mismo valor. El backend probablemente solo necesita uno. Además, `session_id` debería ser `sessionId` (camelCase según convenciones JS).

#### vision.js (líneas 34-37):

```javascript
formData.append('image', file);
const currentOp = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
formData.append('operator_id', currentOp);
```

**Problema**: Enviando `operator_id` como nombre de campo. Dependiendo del `DiagnosticRequestSerializer` del backend, podría ser:
- `operator` (si FK a User)
- `operator_id` (si IntegerField)

#### crops.js (líneas 102-107):

```javascript
const newPlantData = {
    usuario: currentUser,    // ⚠️ Key inconsistency
    nombre: safePlantName,
    tipo: plantType,
    timestamp: Date.now()
};
```

**Problema**: Enviando `usuario` pero el serializer podría esperar `user`, `owner`, o `user_id`.

#### crops.js (línea 111):

```javascript
const response = await fetch(`${window.AppConfig.API_BASE_URL}/plants/register`, {
```

**Problema**: Endpoint sin trailing slash (`/plants/register` vs `/plants/register/`). Puede causar 301 redirects o 404.

### 3.3 Formatos de Archivo

admin.html especifica:

| Campo Input | accept="" | Expectativa Backend |
|-------------|-----------|---------------------|
| `#mlops-rag-file` | `.pdf,.txt` | ✅ Correcto para RAG |
| `#mlops-cnn-file` | `.zip,image/*` | ⚠️ Mezcla confuse |

**Problema**: `accept=".zip,image/*"` dice ZIP pero aceptacualquier imagen. EI backend espera:
- Solo `.zip` con estructura específica para retraining CNN
- No debe aceptar imágenes sueltas

### 3.4 WebSocket — Estado Actual

El código define configuración PERO NO USA WebSocket activamente:

- `config.js` define `POLLING_INTERVAL: 5000` (5s)
- `tactical.js` tiene `bindWebSocket()` (líneas 115-132) INUTILIZADO
- Dashboard recibe telemetía por polling, NO por WebSocket

**Hallazgo**: La resiliencia de WebSockets está implementada PERO no integrada. El frontend cae a polling sin indicación al usuario.

---

## 4. Estado de FRs y NFRs

### 4.1 Requisitos Funcionales (FR)

| FR | Estado | Evidencia |
|----|--------|----------|
| FR1: Login/Logout de operadores | ✅ CUMPLIDO | login.html + main.js:254-306 |
| FR2: Dashboard con telemetry | ✅ CUMPLIDO | dashboard.html KPIs implementados |
| FR3: Chat con IA copiloto | ✅ CUMPLIDO | chat.js + MS2 integration |
| FR4: Upload de imagen para diagnóstico | ⚠️ PARCIAL | Referenciado pero modal no existe en templates actuales |
| FR5: Búsqueda de flora mexicana | ⚠️ PARCIAL | Funcional en main.js:635-877 pero UI integrada en index.html |
| FR6: Admin MLOps (RAG + CNN retrain) | ✅ CUMPLIDO | admin.html + mlops.js |
| FR7: Registro de plantas | ⚠️ PARCIAL | Funcional en crops.js pero modal no existe |
| FR8: Perfil de operador | ⚠️ PARCIAL | Funcional en iot.js:108-122 pero modal no existe |
| FR9: Historial de diagnósticos | ❌ FALTANTE | Referenciado en MODULES pero no implementado |
| FR10: Mapa de ubicación | ❌ FALTANTE | Reference en MODULES pero no implementado |

### 4.2 Requisitos No Funcionales (NFR)

| NFR | Estado | Observación |
|-----|--------|------------|
| NFR1: Dark Mode táctico | ✅ CUMPLIDO | Palette mole-base completamente implementada |
| NFR2: Responsividad (mobile-first) | ✅ CUMPLIDO | Breakpoints en todas las vistas |
| NFR3: Minimalismo | ⚠️ PARCIAL | UI recargada con scanline overlay y efectos no esenciales |
| NFR4: WebSocket resiliencia | ❌ NO IMPLEMENTADO | bindWebSocket definido pero no usado |
| NFR5: Offline-first | ⚠️ PARCIAL | localStorage usado pero sin sync strategy clara |
| NFR6: Accesibilidad WCAG | ❌ INCUMPLIDO | Múltiples violations (ver sección 2.5) |
| NFR7: Performance (<200ms) | ⚠️ PARCIAL | setInterval sin cleanup causa leaks |
| NFR8: Design System tokens | ⚠️ PARCIAL | Definidos pero no usados consistentemente |

---

## 5. Plan de Refactorización

### Prioridad ALTA

| # | Tarea | Archivo | Razón | Estimación |
|---|-------|---------|--------|-------------|
| A1 |统一izar colores: reemplazar `#00ffaa` → `mole-cyan`, `#f97316` → `mole-amber` | main.js, chat.js | Design System | 2h |
| A2 | Implementar WebSocket activas: integrar `bindWebSocket()` en dashboard | main.js | NFR4 | 4h |
| A3 | Agregar aria-labels y focus states a todos los buttons | *.html | a11y WCAG | 2h |
| A4 | Corregir contratos JSON: normalizar keys (`operator_id` → `operator`, `session_id` → `sessionId`) | vision.js, chat.js, crops.js | Contratos Backend | 1h |
| A5 | Limpiar memory leaks: cleanup de setIntervals en logout | main.js | Performance | 1h |
| A6 | Implementar modales faltantes: FR4 (diagnóstico), FR7 (registro), FR9 (historial) | *.html | Requisitos FR | 8h |

### Prioridad MEDIA

| # | Tarea | Archivo | Razón | Estimación |
|---|-------|---------|--------|-------------|
| M1 | Extraer createNode functions a módulo utilitario | dom.js | Modularidad | 2h |
| M2 | Eliminar Object.assign(window, ...) y usar imports normalizados | main.js | Clean Code | 3h |
| M3 | Consolidar Toast: eliminar duplicación apiService.showToast + tactical.showTacticalToast | apiService.js, tactical.js | DRY | 1h |
| M4 | Corregir endpoint consistency: agregar trailing slashes | crops.js | Backend contract | 30m |
| M5 | Implementar keyboard navigation para botones "[ENTER]" | index.html | a11y | 30m |
| M6 | Optimizar renderPlantResults: usar DocumentFragment | main.js | Performance | 1h |
| M7 | Corregir accept=".zip,image/*" → solo ".zip" | admin.html | Backend contract | 15m |

### Prioridad BAJA

| # | Tarea | Archivo | Razón | Estimación |
|---|-------|---------|--------|-------------|
| B1 | Extraer inline SVGs a sprite o componente Icon | *.html | Mantenibilidad | 2h |
| B2 | Remover scanline overlay si no agrega valor funcional | *.html | Minimalismo | 30m |
| B3 | Agregar sistema de loggingcentralizado | main.js | Debugging | 1h |
| B4 | Documentar API attendue en Swagger/OpenAPI spec | - | Documentación | 2h |
| B5 | Implementar lazy loading para imágenes | dashboard.html | Performance | 30m |

---

## Anexo: Métricas Cuantitativas

- **Total líneas HTML**: ~445 líneas
- **Total líneas JS**: ~1,800+ líneas (módulos)
- **Total CSS lines**: ~50 líneas (main.css) + 2,000+ de compiled
- **Archivos templates**: 4
- **Módulos JS**: 18
- **Hardcoded colors**: ~70 instancias
- **Missing a11y attributes**: ~15 elementos
- **Memory leaks potenciales**: 2 funciones

---

**Fin del Reporte de Auditoría**

*Este documento sirve como base para la planificación del siguiente sprint de refactorización.*