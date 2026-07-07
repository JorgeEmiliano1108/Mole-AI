# ADR-006: Consolidación de Capa API y Estructura de Módulos

**Fecha:** 2026-06-28 (actualizado 2026-07-03)  
**Estado:** Implementado  
**Referencia:** FE-DT16, FE-DT14 F3a, FE-DT17

---

## Contexto

El frontend de Mole-AI tenía varias incoherencias arquitectónicas detectadas durante la auditoría de RF/RNF:

1. **`window.ApiService` legacy** — El cliente HTTP principal vivía en `static/js/apiService.js`, fuera del árbol de módulos ES6, y era cargado por los 4 HTML entry points como script global. Los módulos ES6 en `src/js/modules/` lo consumían como global sin import explícito.

2. **`sessionManager.js` huérfano** — En `modules/` raíz, sin pertenecer a ninguna capa (api/services/ui/auth).

3. **Dashboards en `auth/`** — `adminDashboard.js` y `userDashboard.js` estaban en `modules/auth/` sin relación con autenticación.

4. **`navigation.js` violaba capas** — Importaba dinámicamente `services/map.js` desde `ui/`, violando la dirección de dependencias (ui → services es ilegal).

5. **TypeScript huérfano** — `cursor.ts` y `typewriter.ts` existían sin `tsconfig.json`, sin type-checking, en un proyecto JS puro.

6. **`services/iot.js` vs `ui/iot.js`** — Dos archivos con el mismo nombre en capas distintas, con responsabilidades diferentes (BLE provisioning vs wizard modal). No era colisión accidental sino dualidad orquestada por `main.js`, pero no estaba documentada.

---

## Decisión

### 1. Wrapper transicional de ApiService (FE-DT16)

Crear `src/js/modules/api/apiService.js` como wrapper que re-exporta `window.ApiService` (definido por el legacy `static/js/apiService.js`). Esto permite a los módulos ES6 importar apiService como módulo sin cambiar los 4 HTML entry points ni los scripts legacy (`dashboard-sre.js`, `dashboard-chat.js`).

**Condición de cierre:** Cuando `dashboard-sre.js` y `dashboard-chat.js` se migren a módulos ES6, el wrapper debe reemplazarse por un import directo del ApiService real movido a `src/`.

### 2. Reorganización de módulos

| Archivo | Origen | Destino |
|---------|--------|---------|
| sessionManager.js | `modules/sessionManager.js` | `modules/auth/sessionManager.js` |
| adminDashboard.js | `modules/auth/adminDashboard.js` | `modules/dashboard/adminDashboard.js` |
| userDashboard.js | `modules/auth/userDashboard.js` | `modules/dashboard/userDashboard.js` |

### 3. Registry pattern para lazy imports

`navigation.js` exporta `registerLazyLoader(viewId, loaderFn)` para módulos pesados (Leaflet vía `services/map.js`). `main.js` registra el loader. Esto elimina la violación de capas para cargas diferidas.

**FE-DT14 F3a (2026-07-03):** Se relajó parcialmente la regla "ui/ no importa de services/" para funciones ligeras de navegación. `navigation.js` importa directamente `loadWiki` desde `services/wiki.js` e `initIoTView` desde `services/iot.js`. El trade-off aceptado: eliminar 3 bridges `window.*` a costa de reintroducir dependencia directa ui→services. La regla se mantiene para módulos pesados (map.js, chart libraries) que siguen usando `registerLazyLoader`.

### 4. TypeScript → JavaScript

`cursor.ts` y `typewriter.ts` convertidos a `.js` con eliminación de anotaciones de tipo. Vite compila TS internamente vía esbuild, pero sin `tsconfig.json` no hay type-checking. La conversión elimina la falsa sensación de seguridad que daban los tipos sin verificación.

### 5. Documentación de dualidad iot.js

`docs/requisitos.md §8` documenta explícitamente que `services/iot.js` (BLE provisioning) y `ui/iot.js` (wizard modal) son archivos distintos con responsabilidades separadas, ambos orquestados por `main.js`.

---

## Consecuencias

**Positivas:**
- Las 5 capas ahora son coherentes: `api/`, `auth/`, `dashboard/`, `services/`, `ui/`
- `sessionManager.js` está donde pertenece (auth/)
- Las dashboards están donde pertenecen (dashboard/)
- `navigation.js` ya no viola la dirección de capas
- Zero archivos `.ts` sin type-checking
- La dualidad `iot.js` está documentada, no es una sorpresa para futuros mantenedores

**Negativas:**
- FE-DT16 estuvo abierta hasta migrar scripts legacy (2026-06-28: cerrada)
- El wrapper de apiService añadió un nivel de indirección (eliminado el 2026-07-03 en FE-DT14 — imports directos a `ApiService.js`)
- main.js ganó dos imports (sre.js, chatWidget.js) y una línea de lazy loader (aceptable)
- navigation.js importa de services/ (loadWiki, initIoTView): violación controlada de capas, aceptada para eliminar bridges window.* en FE-DT14 F3a

---

## Cumplimiento

- Test suite: 30/30 ✅
- Audit script: GREEN ✅
- Bundle size: 610 modules, 101 KB main chunk. Barrel `apiService.js` eliminado en FE-DT14 (imports migrados directo a `ApiService.js`)
- `check-docs-consistency.sh`: GREEN ✅
