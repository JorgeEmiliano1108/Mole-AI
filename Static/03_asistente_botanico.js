// ==========================================================
// 3. ASISTENTE BOTÁNICO (SISTEMA MULTI-MODELO) - 100% FUNCIONAL
// ==========================================================

// Definición de los 3 Motores de IA (Cerebros)
const IA_ENGINES = {
    CHAT: 'conversational-botanist', // IA de texto y consejos
    VISION: 'vision-analyzer',       // IA para diagnóstico por foto (Módulo 8)
    STATS: 'statistical-expert'      // IA para análisis de gráficas y sensores (Módulo 4)
};

const defaultChat = `<div class="text-[#00ffaa] opacity-80">> NÚCLEO IA EN LÍNEA...</div>
<div class="text-[#f97316]">> MOLE-IA: Saludos, Operador. Mis 3 motores (Chat, Visión y Estadística) están listos.</div>`;

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
    const engine = forcedEngine || IA_ENGINES.CHAT; // Por defecto usa el chat

    if (!query) return;

    // 1. Mostrar mensaje en UI (Solo si el usuario escribió manualmente)
    if (!customPrompt) {
        chatMessages.innerHTML += `<div class="text-white text-right opacity-80 mb-2">> USUARIO: ${query}</div>`;
        input.value = '';
    }
    
    // Indicador de "Pensando" dinámico según el motor
    const typingId = 'typing-' + Date.now();
    chatMessages.innerHTML += `<div id="${typingId}" class="text-[#00ffaa] opacity-50 animate-pulse">> [${engine.toUpperCase()}] PROCESANDO...</div>`;
    chatMessages.scrollTop = chatMessages.scrollHeight;
    saveChatHistory(); 

    try {
        // 2. CONEXIÓN REAL CON BACKEND
        // Cambia 'http://localhost:3000' por la URL de tu servidor
        const response = await fetch('http://localhost:3000/api/chat/process', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('moleia_token')}`
            },
            body: JSON.stringify({ 
                prompt: query,
                engine: engine, // El servidor decide qué modelo de IA usar
                user: localStorage.getItem('moleia_current_user'),
                history: localStorage.getItem('moleia_chat_history') 
            })
        });

        const data = await response.json();
        
        // 3. Remover indicador y mostrar respuesta real
        const typingElement = document.getElementById(typingId);
        if(typingElement) typingElement.remove();

        if (response.ok) {
            chatMessages.innerHTML += `<div class="text-[#f97316] mb-4">> MOLE-IA: ${data.reply}</div>`;
        } else {
            throw new Error(data.error || "Fallo en enlace.");
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