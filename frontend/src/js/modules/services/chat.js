import { moleApi } from '../api/apiService.js';
// ==========================================================
// 3. ASISTENTE BOTÁNICO (SISTEMA MULTI-MODELO) - 100% FUNCIONAL
// ==========================================================

// Definición de los 3 Motores de IA (Cerebros)
export const IA_ENGINES = {
    CHAT: 'conversational-botanist', // IA de texto y consejos
    VISION: 'vision-analyzer',       // IA para diagnóstico por foto (Módulo 8)
    STATS: 'statistical-expert'      // IA para análisis de gráficas y sensores (Módulo 4)
};

export let chatMessagesData = [];

export function loadChatHistory() {
    const chatBox = document.getElementById('chat-messages');
    if (!chatBox) return;

    chatBox.textContent = '';
    const saved = localStorage.getItem('moleia_chat_history_data');
    if (saved) {
        try {
            chatMessagesData = JSON.parse(saved);
        } catch (e) {
            chatMessagesData = [];
        }
    }
    
    if (chatMessagesData.length === 0) {
        chatMessagesData.push({ type: 'sys', text: '> NÚCLEO IA EN LÍNEA...' });
        chatMessagesData.push({ type: 'bot', text: '> MOLE-IA: Saludos, Operador. Mis 3 motores (Chat, Visión y Estadística) están listos.' });
    }

    chatMessagesData.forEach(msg => {
        let className = '';
        if (msg.type === 'sys') className = 'text-[#00ffaa] opacity-80';
        else if (msg.type === 'bot') className = 'text-[#f97316] mb-4';
        else if (msg.type === 'user') className = 'text-white text-right opacity-80 mb-2';
        else if (msg.type === 'error') className = 'text-red-500';
        
        chatBox.appendChild(createNode('div', className, msg.text));
    });
    chatBox.scrollTop = chatBox.scrollHeight;
}

export function saveChatHistory() {
    localStorage.setItem('moleia_chat_history_data', JSON.stringify(chatMessagesData));
}

export function toggleChat() {
    const chatWindow = document.getElementById('chat-window');
    if (!chatWindow) return;
    chatWindow.classList.toggle('hidden');
    chatWindow.classList.toggle('flex');
    if (!chatWindow.classList.contains('hidden')) {
        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
        document.getElementById('chat-input')?.focus();
    }
}

async function sendChatMessage(customPrompt = null, forcedEngine = null) {
    const input = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    const query = customPrompt || input.value.trim();
    const engine = forcedEngine || IA_ENGINES.CHAT; 

    if (!query) return;

    if (!customPrompt) {
        const text = `> USUARIO: ${query}`;
        chatMessagesData.push({ type: 'user', text: text });
        chatMessages.appendChild(createNode('div', 'text-white text-right opacity-80 mb-2', text));
        input.value = '';
    }

    const typingId = 'typing-' + Date.now();
    const typingNode = createNode('div', 'text-[#00ffaa] opacity-50 animate-pulse', `> [${engine.toUpperCase()}] PROCESANDO...`, { id: typingId });
    chatMessages.appendChild(typingNode);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    saveChatHistory(); 
    
    // Deshabilitar input
    if (input) {
        input.disabled = true;
        input.classList.add('opacity-50', 'cursor-not-allowed');
    }

    try {
        const data = await moleApi.post('chat/', {
            question: query,
            prompt: query,
            engine: engine,
            session_id: localStorage.getItem('moleia_current_user') || 'anon'
        });
        
        const typingElement = document.getElementById(typingId);
        if(typingElement) typingElement.remove();

        const serverReply = data.answer || data.reply || data.response || "Análisis completado.";
        const text = `> MOLE-IA: ${serverReply}`;
        chatMessagesData.push({ type: 'bot', text: text });
        chatMessages.appendChild(createNode('div', 'text-[#f97316] mb-4', text));
        
        if (data.disclaimer) {
            window.dispatchEvent(new CustomEvent('disclaimerReceived', { detail: { text: data.disclaimer } }));
        }

    } catch (error) {
        console.error("Error en motor IA:", error);
        document.getElementById(typingId)?.remove();
        const text = `> ERROR: Enlace neuronal con ${engine} interrumpido.`;
        chatMessagesData.push({ type: 'error', text: text });
        chatMessages.appendChild(createNode('div', 'text-red-500', text));
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
    saveChatHistory(); 
    
    // Habilitar input
    if (input) {
        input.disabled = false;
        input.classList.remove('opacity-50', 'cursor-not-allowed');
        input.focus();
    }
}

/**
 * PROTOCOLO DE CONEXIÓN CON OTROS MÓDULOS
 */

// Se llama desde el Módulo 8 (Cámara)
export function requestVisionAnalysis(species) {
    toggleChat();
    sendChatMessage(`Analiza la salud de mi ${species} basándote en la captura actual.`, IA_ENGINES.VISION);
}

// Se llama desde el Módulo 4 (Gráficas)
export function requestStatsAnalysis() {
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