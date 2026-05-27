// ==========================================================
// 13. SEGURIDAD S1: CONTROL DE MEMORIA Y LISTENERS [ESTRICTO]
// ==========================================================

// Variable de estado global para evitar oyentes duplicados (Fugas de memoria)
export let chatListenerAttached = false;

/**
 * CONEXI N SEGURA: Conecta el canal de escucha del chat UNA SOLA VEZ.
 * Vital para recibir eventos de WebSockets (Socket.io) o SSE sin clonar mensajes.
 */
export function attachChatListenerOnce() {
    if (chatListenerAttached) {
        console.warn("> [!] ALERTA DE SISTEMA: Intento de duplicar listener del chat interceptado y bloqueado.");
        return;
    }

    // Aseguramos que la funci n receptora exista antes de atar el evento
    if (typeof handleChatResponse === 'function') {
        window.addEventListener('chatMessage', handleChatResponse);
        chatListenerAttached = true;
        console.log("> [ OK ] Protocolo de escucha de chat activado y asegurado.");
    } else {
        console.error("> [ ERROR CR\u00cdTICO ] Funci\u00f3n 'handleChatResponse' no definida. El enlace de comunicaci\u00f3n est\u00e1 roto.");
    }
}

/**
 * DESCONEXI N T CTICA: Libera la RAM y cierra los canales de escucha.
 * Se invoca din micamente cuando el usuario oculta/cierra la interfaz de comunicaci n.
 */
export function detachChatListener() {
    if (!chatListenerAttached) return;

    if (typeof handleChatResponse === 'function') {
        window.removeEventListener('chatMessage', handleChatResponse);
        chatListenerAttached = false;
        console.log("> [ OK ] Listener de chat desconectado (Memoria RAM liberada con \u00e9xito).");
    }
}

/**
 * PROTOCOLO DE DESTRUCCI N ("GARBAGE COLLECTION"): 
 * Limpia los procesos activos cuando el usuario cierra o recarga la pesta a.
 * Evita conexiones fantasma que saturen el cl ster del Backend Central.
 */
window.addEventListener('beforeunload', () => {
    console.log("> Iniciando protocolo de apagado del sistema MOLE-IA...");
    
    // 1. Cortamos el canal del chat
    detachChatListener();
    
    // 2. Apagamos los sensores de telemetr a continua (Polling de datos del huerto)
    if (typeof window.monitorInterval !== 'undefined' && window.monitorInterval) {
        clearInterval(window.monitorInterval);
        console.log("> [ OK ] Intervalo de telemetr\u00eda de sensores destruido.");
    }

    // 3. (Backend Estricto) Desconexi n forzada de WebSockets si estuvieran activos:
    if (typeof window.socketInstance !== 'undefined' && window.socketInstance) {
        window.socketInstance.disconnect();
        console.log("> [ OK ] Socket de conexi\u00f3n en tiempo real cerrado.");
    }
});