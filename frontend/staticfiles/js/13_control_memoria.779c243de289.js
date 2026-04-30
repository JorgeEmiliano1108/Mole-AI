// ==========================================================
// 13. SEGURIDAD S1: CONTROL DE MEMORIA Y LISTENERS [ESTRICTO]
// ==========================================================

// Variable de estado global para evitar oyentes duplicados (Fugas de memoria)
let chatListenerAttached = false;

/**
 * CONEXIÓN SEGURA: Conecta el canal de escucha del chat UNA SOLA VEZ.
 * Vital para recibir eventos de WebSockets (Socket.io) o SSE sin clonar mensajes.
 */
function attachChatListenerOnce() {
    if (chatListenerAttached) {
        console.warn("> [!] ALERTA DE SISTEMA: Intento de duplicar listener del chat interceptado y bloqueado.");
        return;
    }

    // Aseguramos que la función receptora exista antes de atar el evento
    if (typeof handleChatResponse === 'function') {
        window.addEventListener('chatMessage', handleChatResponse);
        chatListenerAttached = true;
        console.log("> [ OK ] Protocolo de escucha de chat activado y asegurado.");
    } else {
        console.error("> [ ERROR CRÍTICO ] Función 'handleChatResponse' no definida. El enlace de comunicación está roto.");
    }
}

/**
 * DESCONEXIÓN TÁCTICA: Libera la RAM y cierra los canales de escucha.
 * Se invoca dinámicamente cuando el usuario oculta/cierra la interfaz de comunicación.
 */
function detachChatListener() {
    if (!chatListenerAttached) return;

    if (typeof handleChatResponse === 'function') {
        window.removeEventListener('chatMessage', handleChatResponse);
        chatListenerAttached = false;
        console.log("> [ OK ] Listener de chat desconectado (Memoria RAM liberada con éxito).");
    }
}

/**
 * PROTOCOLO DE DESTRUCCIÓN ("GARBAGE COLLECTION"): 
 * Limpia los procesos activos cuando el usuario cierra o recarga la pestaña.
 * Evita conexiones fantasma que saturen el clúster del Backend Central.
 */
window.addEventListener('beforeunload', () => {
    console.log("> Iniciando protocolo de apagado del sistema MOLE-IA...");
    
    // 1. Cortamos el canal del chat
    detachChatListener();
    
    // 2. Apagamos los sensores de telemetría continua (Polling de datos del huerto)
    if (typeof window.monitorInterval !== 'undefined' && window.monitorInterval) {
        clearInterval(window.monitorInterval);
        console.log("> [ OK ] Intervalo de telemetría de sensores destruido.");
    }

    // 3. (Backend Estricto) Desconexión forzada de WebSockets si estuvieran activos:
    if (typeof window.socketInstance !== 'undefined' && window.socketInstance) {
        window.socketInstance.disconnect();
        console.log("> [ OK ] Socket de conexión en tiempo real cerrado.");
    }
});