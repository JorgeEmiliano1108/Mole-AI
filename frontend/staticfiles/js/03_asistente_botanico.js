// ==========================================================
// 3. ASISTENTE BOTÁNICO (SISTEMA MULTI-MODELO) - 100% FUNCIONAL
// ==========================================================

// Definición de los 3 Motores de IA (Cerebros)
const IA_ENGINES = {
    CHAT: 'conversational-botanist', // IA de texto y consejos
    VISION: 'vision-analyzer',       // IA para diagnóstico por foto (Módulo 8)
    STATS: 'statistical-expert'      // IA para análisis de gráficas y sensores (Módulo 4)
};

const defaultChat = `<div class="text-[#00e5ff] opacity-80">> NÚCLEO IA EN LÍNEA...</div>
<div class="text-[#FBBF24]">> MOLE-IA: Saludos, Operador. Mis 3 motores (Chat, Visión y Estadística) están listos.</div>`;

/**
 * CARGA DE HISTORIAL: Recupera la conversación del almacenamiento local.
 */
function loadChatHistory() {
    const chatBox = document.getElementById('chat-messages');
    if (!chatBox) return;

    const savedChat = localStorage.getItem('moleia_chat_history');
    chatBox.innerHTML = savedChat ? savedChat : defaultChat;
    chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * GUARDADO DE HISTORIAL
 */
function saveChatHistory() {
    const chatBox = document.getElementById('chat-messages');
    if (chatBox) {
        localStorage.setItem('moleia_chat_history', chatBox.innerHTML);
    }
}

/**
 * TOGGLE UI
 */
function toggleChat() {
    const chatWindow = document.getElementById('chat-window');
    if (!chatWindow) return;
    chatWindow.classList.toggle('hidden');
    chatWindow.classList.toggle('flex');
    if (!chatWindow.classList.contains('hidden')) {
        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
        document.getElementById('chat-input')?.focus();
    }
}

/**
 * FUNCIÓN MAESTRA: ENVÍO DE MENSAJES (Soporta los 3 modelos)
 * @param {string} customPrompt - Si se envía texto desde otro módulo (ej. análisis automático).
 * @param {string} forcedEngine - Fuerza el uso de VISION o STATS.
 */
async function sendChatMessage(customPrompt = null, forcedEngine = null) {
    const input = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    const query = customPrompt || input.value.trim();
    const engine = forcedEngine || IA_ENGINES.CHAT; 

    if (!query) return;

    if (!customPrompt) {
        chatMessages.innerHTML += `<div class="text-white text-right opacity-80 mb-2">> USUARIO: ${query}</div>`;
        input.value = '';
    }
    
    const typingId = 'typing-' + Date.now();
    chatMessages.innerHTML += `<div id="${typingId}" class="text-[#00e5ff] opacity-50 animate-pulse">> [${engine.toUpperCase()}] PROCESANDO...</div>`;
    chatMessages.scrollTop = chatMessages.scrollHeight;
    saveChatHistory(); 

    try {
        // 🚀 USO DE API SERVICE: Interceptamos 'chat_fallback/' o 'chat/' según tus URLs de backend
        // Enviamos 'question' porque así lo espera tu backend en Django
        const data = await window.moleApi.post('chat/', {
            question: query,
            prompt: query,     // Mantenemos prompt por compatibilidad futura
            engine: engine,
            session_id: localStorage.getItem('moleia_current_user') || 'anon'
        });
        
        const typingElement = document.getElementById(typingId);
        if(typingElement) typingElement.remove();

        // Extraemos la respuesta mapeando las distintas formas en que tu backend puede contestar
        const serverReply = data.answer || data.reply || data.response || "Análisis completado.";
        
        chatMessages.innerHTML += `<div class="text-[#FBBF24] mb-4">> MOLE-IA: ${serverReply}</div>`;
        
        // Disparamos evento si trae disclaimer médico (COFEPRIS Fase 3)
        if (data.disclaimer) {
            window.dispatchEvent(new CustomEvent('disclaimerReceived', { detail: { text: data.disclaimer } }));
        }

    } catch (error) {
        console.error("Error en motor IA:", error);
        document.getElementById(typingId)?.remove();
        chatMessages.innerHTML += `<div class="text-red-500">> ERROR: Enlace neuronal con ${engine} interrumpido.</div>`;
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
    saveChatHistory(); 
}

/**
 * PROTOCOLO DE CONEXIÓN CON OTROS MÓDULOS
 */

// Se llama desde el Módulo 8 (Cámara)
function requestVisionAnalysis(species) {
    toggleChat();
    sendChatMessage(`Analiza la salud de mi ${species} basándote en la captura actual.`, IA_ENGINES.VISION);
}

// Se llama desde el Módulo 4 (Gráficas)
function requestStatsAnalysis() {
    toggleChat();
    sendChatMessage(`Genera un reporte analítico de los sensores de la última semana.`, IA_ENGINES.STATS);
}

// Listener para el teclado
document.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    document.getElementById('chat-input')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendChatMessage();
    });
});