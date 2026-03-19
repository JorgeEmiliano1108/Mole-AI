# LEGACY FRONTEND ARCHITECTURE & CONTEXT REPORT

**Proyecto:** Mole.AI Legacy Frontend (Vanilla JS)  
**Fecha:** 16 de marzo de 2026  
**Rol de auditoría:** Senior Vanilla JS Architect & Security Auditor  
**Restricción de arquitectura:** Mantener HTML5 + CSS3 + ES6 puro (sin migración a frameworks)

---

## 1. Estado Actual (Current State)

### 1.1 Stack tecnológico real

- Frontend monolítico en Vanilla JS, sin bundler y sin gestor de paquetes frontend.
- Render principal servido por Django Template en [templates/index.html](templates/index.html).
- Lógica principal en [static/js/main.js](static/js/main.js).
- Capa de red y WebSocket en [static/js/apiService.js](static/js/apiService.js).
- Configuración runtime en [static/js/config.js](static/js/config.js).
- Estilos en [static/css/styles.css](static/css/styles.css).
- Dependencias externas por CDN:
  - Supabase JS SDK.
  - Leaflet + OpenStreetMap.
  - Google Font VT323.

### 1.2 Pantallas y vistas actuales

Pantallas principales detectadas en [templates/index.html](templates/index.html):

- Start Screen: selector de introducción y botón iniciar sistema.
  - Nodo: start-screen.
  - Menú: Objetivo, Visión, Flora Mexicana, Acerca.
- Login Screen: autenticación y registro.
  - Nodo: login-screen.
  - Campos login: email y password.
  - Campos registro: username y fecha de nacimiento.
- App Screen: monitoreo principal.
  - Nodo: app-screen.
  - Tabs de plantas: 9 especies.
  - Panel de sensores: humedad, temperatura, pH, UV, estado.
  - Mapa fitosanitario embebido (Leaflet).
  - Modal de chat IA con adjunto de imagen y estado WebSocket.

Flujo de navegación actual:

1. Start Screen.
2. Login o Registro.
3. App Screen.
4. Interacciones: tabs de planta, mapa, chat, carga de imagen.
5. Salida por recarga completa de página con botón X.

### 1.3 Manejo de estado global actual

Estado global identificado en [static/js/main.js](static/js/main.js) y [static/js/config.js](static/js/config.js):

- pendingImageBase64: imagen pendiente en base64.
- pendingImageLat y pendingImageLon: coordenadas capturadas al adjuntar imagen.
- plantaActual: planta seleccionada.
- monitorInterval: handle de sondeo periódico de sensores.
- typingTimer: temporizador de máquina de escribir del intro.
- window.supabaseClient: cliente Supabase global.
- window.apiService: servicio API global.
- window.APP_CONFIG: configuración global de URLs y credenciales públicas.

Patrón de estado:

- Mutación directa de variables globales.
- Sin store central, sin namespaces por módulo, sin aislamiento por componente.
- Persistencia de sesión delegada al SDK de Supabase.

### 1.4 Endpoints backend actualmente consumidos por el frontend legacy

#### Tabla exacta de consumo

| Funcionalidad | Método | Endpoint real | Dónde se llama | Observaciones |
|---|---|---|---|---|
| Monitoreo de sensores en vivo | GET | /api/v1/sensors/live | [static/js/main.js](static/js/main.js#L225) | Polling cada 5s. Usa AI_API_URL. |
| Chat fallback | POST | /api/v1/chat/fallback/ | [static/js/apiService.js](static/js/apiService.js#L317) | Se activa si WS falla o timeout 10s. |
| Envío de diagnóstico con imagen | POST | /api/v1/diagnostics/ | [static/js/main.js](static/js/main.js#L320) | FormData con image, plant_id, lat/lon opcional. |
| Marcadores geolocalizados | GET | /api/v1/diagnosticos/geolocalizados/ | [static/js/main.js](static/js/main.js#L466) | Renderiza puntos en mapa Leaflet. |
| Chat en tiempo real | WEBSOCKET | /ws/chat/ | [static/js/apiService.js](static/js/apiService.js#L191) | Envía token como query param. |

#### Configuración de URLs: hardcoded vs variables

- API base se resuelve por hostname en runtime, no por archivo .env frontend:
  - Local: http://127.0.0.1:8000/api/v1/
  - Local AI: http://127.0.0.1:8001/api/v1/
  - Producción: /api/v1/
- Supabase URL y ANON KEY están definidos de forma fija en [static/js/config.js](static/js/config.js#L16).

#### Manejo de autenticación y JWT

- Login y registro por Supabase desde [static/js/main.js](static/js/main.js#L116).
- El token se obtiene con supabase.auth.getSession en [static/js/apiService.js](static/js/apiService.js#L32).
- El token se inyecta como Authorization Bearer en headers por buildHeaders en [static/js/apiService.js](static/js/apiService.js#L57).
- En WebSocket se envía como query token en [static/js/apiService.js](static/js/apiService.js#L193).
- Almacenamiento del token: interno del SDK de Supabase (no hay manejo manual explícito en código legacy).

---

## 2. Remediación de Vulnerabilidades (Sin Rewrite)

## 2.1 Vulnerabilidad XSS en chat

### Hallazgos de riesgo

Uso de innerHTML con contenido dinámico en [static/js/main.js](static/js/main.js):

- Burbuja usuario: línea aproximada 344.
- Mensajes de estado: línea aproximada 373.
- Respuesta bot: línea aproximada 404.
- Error bot: línea aproximada 423.

Riesgo:

- Inyección HTML/JS si el contenido contiene etiquetas o payloads maliciosos.
- Riesgo elevado cuando respuestas provienen de servicios externos o entradas de usuario.

### Solución exacta en Vanilla JS puro

Objetivo: eliminar concatenación con innerHTML para contenido no confiable.

#### Paso A: crear helper seguro de render de mensajes

    function appendChatMessage(container, role, text, opts = {}) {
        const msg = document.createElement('div');
        msg.className = 'ai-message ' + role + (opts.extraClass ? ' ' + opts.extraClass : '');

        if (opts.withImage && opts.imageSrc) {
            const img = document.createElement('img');
            img.className = 'image-in-chat';
            img.alt = 'Imagen enviada';
            img.src = opts.imageSrc;
            msg.appendChild(img);
        }

        const textNode = document.createElement('div');
        textNode.className = 'chat-text';
        textNode.textContent = text || '';
        msg.appendChild(textNode);

        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
        return msg;
    }

#### Paso B: reemplazar burbuja usuario

Reemplazar bloque de línea aproximada 338 a 345 en [static/js/main.js](static/js/main.js#L338):

    appendChatMessage(chatContainer, 'user', question || '(imagen adjunta)', {
        withImage: !!pendingImageBase64,
        imageSrc: pendingImageBase64
    });

#### Paso C: reemplazar mensajes de estado

Reemplazar uso de innerHTML en estado por nodo seguro:

    const statusEl = appendChatMessage(chatContainer, 'bot', data.message || '', { extraClass: 'status' });
    setTimeout(() => {
        if (statusEl && statusEl.parentNode) statusEl.parentNode.removeChild(statusEl);
    }, 3000);

#### Paso D: reemplazar render de respuesta bot sin HTML crudo

En vez de convertir saltos a br vía HTML, crear líneas por texto:

    function appendMultilineBotMessage(container, answer, tacticalCount) {
        const wrapper = document.createElement('div');
        wrapper.className = 'ai-message bot';

        if (tacticalCount > 0) {
            const badge = document.createElement('div');
            badge.className = 'tactical-alert-indicator';
            badge.textContent = 'ALERTA: ' + tacticalCount + ' alertas tácticas';
            wrapper.appendChild(badge);
        }

        const lines = String(answer || '').split('\n');
        lines.forEach((line, idx) => {
            const p = document.createElement('p');
            p.textContent = line;
            wrapper.appendChild(p);
            if (idx < lines.length - 1) {
                const spacer = document.createElement('br');
                wrapper.appendChild(spacer);
            }
        });

        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;
    }

#### Paso E: remover chequeo basado en innerHTML.includes

Reemplazar detección de alerta táctica (línea aproximada 408) por clase explícita cuando tacticalCount sea mayor a cero.

---

## 2.2 Fuga de memoria por Event Listeners y timers

### Hallazgos de riesgo

- Listener de chat agregado en cada envío sin cleanup en [static/js/main.js](static/js/main.js#L358).
- No se elimina listener al cerrar chat o al descargar página.
- monitorInterval se asigna en iniciarMonitoreoReal sin clear defensivo en [static/js/main.js](static/js/main.js#L221).

### Solución exacta en Vanilla JS puro

#### Paso A: registrar listener una sola vez

Agregar bandera global:

    let chatListenerAttached = false;

En inicialización (DOMContentLoaded), no en cada enviar:

    function attachChatListenerOnce() {
        if (chatListenerAttached) return;
        window.addEventListener('chatMessage', handleChatResponse);
        chatListenerAttached = true;
    }

    function detachChatListener() {
        if (!chatListenerAttached) return;
        window.removeEventListener('chatMessage', handleChatResponse);
        chatListenerAttached = false;
    }

Llamar attachChatListenerOnce al abrir chat o al iniciar app. Eliminar la línea actual que lo agrega dentro de enviarComandoAI.

#### Paso B: cleanup al cerrar chat y al salir

En cerrarChat:

    function cerrarChat() {
        document.getElementById('ai-modal').style.display = 'none';
        detachChatListener();
    }

En lifecycle global:

    window.addEventListener('beforeunload', () => {
        detachChatListener();
        if (window.apiService) window.apiService.closeWebSocket();
        if (monitorInterval) {
            clearInterval(monitorInterval);
            monitorInterval = null;
        }
    });

#### Paso C: blindaje de intervalos de monitoreo

Reemplazar iniciarMonitoreoReal por versión segura:

    function iniciarMonitoreoReal() {
        if (monitorInterval) {
            clearInterval(monitorInterval);
            monitorInterval = null;
        }
        fetchSensorData();
        monitorInterval = setInterval(fetchSensorData, 5000);
    }

#### Paso D: evitar listeners inline en HTML nuevo

Para nuevas pantallas, evitar onclick en atributos y migrar gradualmente a addEventListener por nodos en inicialización para controlar mejor altas y bajas.

---

## 3. Mapeo de Brechas (Gaps vs Nuevo Backend Fase 2)

## 3.1 Gaps obligatorios solicitados

| Requisito | Backend disponible | Estado frontend legacy | Acción requerida en Vanilla JS |
|---|---|---|---|
| Eliminar cuenta ARCO | DELETE /api/v1/auth/profile/ | No implementado | Agregar botón Eliminar cuenta con confirmación doble y llamada API autenticada. |
| Mapa AgroGuard Hotspots | GET /api/v1/map/hotspots/ | No implementado | Nueva pantalla o panel Hotspots con filtros days, pest, precision y capa de clusters. |
| FeedbackTicket | POST /api/v1/feedback/ | No implementado | Formulario/modal con topic y message; validaciones cliente y manejo de errores. |
| Disclaimer COFEPRIS visible en chat | Backend lo inyecta en respuesta | No hay componente dedicado ni fijación visual | Crear bloque fijo de aviso legal en UI de chat y estilo destacado. |
| Onboarding Wi-Fi ESP32 | Flujo frontend inexistente | No implementado | Crear wizard UI para credenciales Wi-Fi y emparejamiento de dispositivo (flujo conceptual en 3.3). |

## 3.2 Otras brechas funcionales detectadas

| Endpoint backend | Estado en frontend | Gap |
|---|---|---|
| GET/PATCH /api/v1/auth/profile/ | No consumido | No hay pantalla de perfil editable. |
| GET/PUT /api/v1/auth/subscription/ | No consumido | No hay panel de estado premium/suscripción. |
| GET /api/v1/auth/metadata/ | No consumido | Sin diagnóstico de sesión ni claims. |
| POST /api/v1/auth/logout/ | No consumido | El botón X recarga la página en vez de logout controlado. |
| POST /api/v1/auth/validate-token/ | No consumido | No handshake explícito frontend-backend tras login Supabase. |
| GET /api/v1/diagnostics/history/ | No consumido | Sin vista de historial. |
| GET /api/v1/diagnostics/<id>/download/ | No consumido | Sin descarga de reporte PDF. |
| GET /api/v1/plant-knowledge/ | No consumido | Sin explorador de conocimiento botánico. |
| GET /api/v1/history/ | No consumido | Sin historial consolidado de actividad. |

## 3.3 Flujo conceptual requerido: Onboarding Wi-Fi ESP32 (UI)

Nota: en este repositorio no hay flujo frontend legado para provisión de Wi-Fi de dispositivo.

### Propuesta de flujo UI en Vanilla JS

1. Pantalla Dispositivo:
   - Buscar ESP32 disponible.
   - Estado de conexión actual.
2. Modal Configurar Wi-Fi:
   - Campos SSID y Password.
   - Selector de región/país opcional para cumplimiento RF.
3. Paso Confirmación:
   - Mostrar resumen antes de enviar.
   - Confirmar y aplicar configuración.
4. Validación:
   - Mostrar progreso con timeout y reintento.
5. Resultado:
   - Éxito: dispositivo en línea.
   - Error: diagnóstico básico y acción recomendada.

### Requisitos mínimos de seguridad UI para este flujo

- Nunca renderizar password en texto plano.
- No persistir password en localStorage/sessionStorage.
- Limpiar campos sensibles en cierre y navegación.
- Máscara visual y botón mostrar/ocultar temporal.

---

## 4. Lista To-Do para equipo UI/UX + Frontend Vanilla JS

Prioridad ordenada para integración con Backend Fase 2.

### 4.1 Sprint S1 Seguridad (bloqueante)

- Reemplazar concatenación innerHTML en chat por render seguro con createElement y textContent.
- Mover listener de chat a registro único y agregar removeEventListener en cleanup.
- Limpiar intervalos y WebSocket al salir de pantalla o beforeunload.
- Añadir capa de normalización de mensajes de chat para evitar HTML no confiable.

### 4.2 Sprint S2 Compliance y UX crítico

- Implementar botón Eliminar cuenta ARCO conectado a DELETE /api/v1/auth/profile/.
- Agregar modal de confirmación en dos pasos para eliminación irreversible.
- Mostrar Disclaimer Legal COFEPRIS de forma persistente en el modal de chat.
- Cambiar botón X actual por logout real con POST /api/v1/auth/logout/ y limpieza de estado.

### 4.3 Sprint S3 Nuevas pantallas funcionales

- Crear pantalla AgroGuard Hotspots con GET /api/v1/map/hotspots/.
- Crear modal/pantalla de FeedbackTicket con POST /api/v1/feedback/.
- Crear vista Historial de diagnósticos con GET /api/v1/diagnostics/history/.
- Crear acción Descargar PDF en detalle diagnóstico con GET /api/v1/diagnostics/<id>/download/.

### 4.4 Sprint S4 Onboarding IoT

- Implementar wizard Onboarding Wi-Fi ESP32 en 5 pasos.
- Definir contrato API/bridge para provisión de credenciales.
- Añadir estados UI de conexión, timeout, reintento y éxito.

---

## 5. Checklist de implementación mínima aceptable

- Chat sin innerHTML para payload dinámico.
- Sin listeners duplicados por envío de mensaje.
- Sin intervalos huérfanos después de logout o unload.
- Botón ARCO funcional y probado con respuesta 204.
- Vista Hotspots funcional con filtros y clusters.
- Formulario feedback funcional con validación topic y message.
- Disclaimer legal visible de forma estable y no solo como texto embebido de respuesta.
- Flujo de onboarding Wi-Fi definido, maquetado y listo para integración.

---

## 6. Conclusión ejecutiva

El frontend legacy actual sí es aprovechable bajo la política de mantener Vanilla JS, pero requiere hardening inmediato en seguridad de renderizado y ciclo de vida de listeners/timers antes de ampliar funcionalidades de Fase 2.

La ruta recomendada es evolución incremental sobre la base actual:

1. Parchear XSS y memory leaks primero.
2. Activar flujos de compliance y soporte operativo (ARCO, disclaimer, logout real).
3. Incorporar nuevas pantallas API-driven (hotspots, feedback, historial).
4. Cerrar la brecha IoT con onboarding de credenciales Wi-Fi para ESP32.

Con este plan, el equipo puede mantener stack Vanilla JS y alcanzar alineación completa con backend empresarial Fase 2.
