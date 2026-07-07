import { el, safeRender } from '../ui/dom.js';
import { apiService } from '../api/ApiService.js';

// ==========================================================
// 3. ASISTENTE BOT NICO (SISTEMA MULTI-MODELO) - 100% FUNCIONAL
// ==========================================================

// Definici n de los 3 Motores de IA (Cerebros)
export const IA_ENGINES = {
    CHAT: 'conversational-botanist', // IA de texto y consejos
    VISION: 'vision-analyzer',       // IA para diagn stico por foto (M dulo 8)
    STATS: 'statistical-expert'      // IA para an lisis de gr ficas y sensores (M dulo 4)
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
        chatMessagesData.push({ type: 'sys', text: '> N\u00daCLEO IA EN L\u00cdNEA...' });
        chatMessagesData.push({ type: 'bot', text: 'Saludos, Operador. Mis 3 motores (Chat, Visi\u00f3n y Estad\u00edstica) est\u00e1n listos.' });
    }

    chatMessagesData.forEach(appendMessage);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Renderizado de UI (Estilo Terminal CRT)
export function appendMessage(msg, isTyping = false) {
    const chatBox = document.getElementById('chat-messages');
    if (!chatBox) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'flex w-full mb-3 ' + (msg.type === 'user' ? 'justify-end' : 'justify-start');

    if (msg.type === 'bot') {
        const textDiv = document.createElement('div');
        textDiv.className = 'bg-transparent px-2 py-1 text-sm text-mole-text crt-text-glow terminal-text max-w-[90%] uppercase';
        
        if (isTyping) {
            msgDiv.appendChild(textDiv);
            if (msg.id) msgDiv.id = msg.id;
            chatBox.appendChild(msgDiv);
            
            const textToType = '> ' + msg.text.replace('> MOLE-IA: ', '');
            let i = 0;
            textDiv.textContent = '';
            
            const typeInterval = setInterval(() => {
                if (i < textToType.length) {
                    textDiv.textContent = textToType.substring(0, i + 1) + '\u2588';
                    i++;
                    chatBox.scrollTop = chatBox.scrollHeight;
                } else {
                    clearInterval(typeInterval);
                    textDiv.textContent = '';
                    textDiv.appendChild(document.createTextNode(textToType));
                    const cursor = document.createElement('span');
                    cursor.className = 'animate-pulse';
                    cursor.textContent = '\u2588';
                    textDiv.appendChild(cursor);
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            }, 20);
            return;
        } else {
            textDiv.textContent = '> ' + msg.text.replace('> MOLE-IA: ', '');
            const cursor = document.createElement('span');
            cursor.className = 'animate-pulse';
            cursor.textContent = '\u2588';
            textDiv.appendChild(cursor);
            msgDiv.appendChild(textDiv);
        }
    } else if (msg.type === 'user') {
        const textDiv = document.createElement('div');
        textDiv.className = 'bg-transparent px-2 py-1 text-sm text-[#14fdce] crt-text-glow font-mono max-w-[90%] text-right uppercase';
        textDiv.textContent = msg.text;
        msgDiv.appendChild(textDiv);
    } else if (msg.type === 'sys') {
        msgDiv.className = 'flex w-full mb-2 justify-start';
        const textSpan = document.createElement('span');
        textSpan.className = 'text-xs text-[#14fdce]/60 font-mono w-full animate-pulse uppercase';
        textSpan.textContent = msg.text;
        msgDiv.appendChild(textSpan);
    } else if (msg.type === 'error') {
        const textDiv = document.createElement('div');
        textDiv.className = 'bg-red-500/20 text-red-500 border border-red-500 px-2 py-1 text-xs font-mono max-w-[90%] w-full uppercase';
        textDiv.textContent = msg.text;
        msgDiv.appendChild(textDiv);
    }

    if (msg.id) msgDiv.id = msg.id;

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Limpiar y crear nueva conversaci n
export function clearChatHistory() {
    chatMessagesData = [];
    localStorage.removeItem('moleia_chat_history_data');
    
    // Generamos un nuevo sessionId para aislar el contexto en el backend
    localStorage.setItem('moleia_current_session_id', 'ses_' + Date.now());

    const chatBox = document.getElementById('chat-messages');
    if (chatBox) chatBox.textContent = '';
    
    chatMessagesData.push({ type: 'sys', text: '> NUEVA CONVERSACI\u00d3N INICIADA...' });
    chatMessagesData.push({ type: 'bot', text: 'He limpiado mi contexto temporal. \u00bfEn qu\u00e9 te ayudo?' });
    
    saveChatHistory();
    loadChatHistory();
}

export function saveChatHistory() {
    localStorage.setItem('moleia_chat_history_data', JSON.stringify(chatMessagesData));
}

export function toggleChat() {
    const chatWindow = document.getElementById('chat-window');
    if (!chatWindow) return;
    // Detectar estado por style.transform (el panel usa inline styles)
    const isOpen = chatWindow.style.transform === 'translateX(0px)' || chatWindow.style.transform === 'translateX(0)';
    if (isOpen) {
        chatWindow.style.transform = 'translateX(100%)';
    } else {
        chatWindow.style.transform = 'translateX(0)';
        const msgs = document.getElementById('chat-messages');
        if (msgs) msgs.scrollTop = msgs.scrollHeight;
        setTimeout(() => document.getElementById('chat-input')?.focus(), 350);
    }
}

export function openChat() {
    const chatWindow = document.getElementById('chat-window');
    if (!chatWindow) return;
    chatWindow.style.transform = 'translateX(0)';
    const msgs = document.getElementById('chat-messages');
    if (msgs) msgs.scrollTop = msgs.scrollHeight;
    setTimeout(() => document.getElementById('chat-input')?.focus(), 350);
}

export function closeChat() {
    const chatWindow = document.getElementById('chat-window');
    if (!chatWindow) return;
    chatWindow.style.transform = 'translateX(100%)';
}


export async function sendChatMessage(customPrompt = null, forcedEngine = null) {
    const input = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    const query = customPrompt || input.value.trim();
    const engine = forcedEngine || IA_ENGINES.CHAT; 

    if (!query) return;

    if (!customPrompt) {
        const text = `> USUARIO: ${query}`;
        chatMessagesData.push({ type: 'user', text: text });
        appendMessage(chatMessagesData[chatMessagesData.length - 1]);
        input.value = '';
    }

    const typingId = 'typing-' + Date.now();
    appendMessage({ type: 'sys', text: `> [${engine.toUpperCase()}] PROCESANDO...`, id: typingId });
    saveChatHistory(); 
    
    // Deshabilitar input
    if (input) {
        input.disabled = true;
        input.classList.add('opacity-50', 'cursor-not-allowed');
    }

    try {
        const activeSessionId = localStorage.getItem('moleia_current_session_id') || localStorage.getItem('moleia_current_user') || 'anon';
        
        const data = await apiService.post('llm/chat/', {
            prompt: query,
            engine: engine,
            sessionId: activeSessionId
        }, { silent: true });
        
        const typingElement = document.getElementById(typingId);
        if(typingElement) typingElement.remove();

        const serverReply = data.answer || data.reply || data.response || "An\u00e1lisis completado.";
        chatMessagesData.push({ type: 'bot', text: serverReply });
        appendMessage(chatMessagesData[chatMessagesData.length - 1], true);
        
        if (data.disclaimer) {
            window.dispatchEvent(new CustomEvent('disclaimerReceived', { detail: { text: data.disclaimer } }));
        }

    } catch (error) {
        console.error("Error en motor IA:", error);
        const typingElement = document.getElementById(typingId);
        if(typingElement) typingElement.remove();
        
        const text = `> ERROR: Enlace neuronal con ${engine} interrumpido.`;
        chatMessagesData.push({ type: 'error', text: text });
        appendMessage(chatMessagesData[chatMessagesData.length - 1]);
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
 * PROTOCOLO DE CONEXI N CON OTROS M DULOS
 */

// Se llama desde el M dulo 8 (C mara)
export function requestVisionAnalysis(species) {
    toggleChat();
    sendChatMessage(`Analiza la salud de mi ${species} bas\u00e1ndote en la captura actual.`, IA_ENGINES.VISION);
}

// Se llama desde el M dulo 4 (Gr ficas)
export function requestStatsAnalysis() {
    toggleChat();
    sendChatMessage(`Genera un reporte anal\u00edtico de los sensores de la \u00faltima semana.`, IA_ENGINES.STATS);
}

// Listener para el teclado y bot n
document.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    document.getElementById('chat-input')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendChatMessage();
    });
    document.getElementById('chat-send-btn')?.addEventListener('click', () => sendChatMessage());
    
    // Listener para el input de visión desde el chat
    const chatVisionInput = document.getElementById('chat-vision-input');
    if (chatVisionInput) {
        chatVisionInput.addEventListener('change', handleChatVisionUpload);
    }
});

async function handleChatVisionUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Reset input
    event.target.value = '';

    const text = `> [VISIÓN] Analizando imagen: ${file.name}...`;
    chatMessagesData.push({ type: 'user', text: text });
    appendMessage(chatMessagesData[chatMessagesData.length - 1]);

    const typingId = 'typing-' + Date.now();
    appendMessage({ type: 'sys', text: `> [VISION-ANALYZER] PROCESANDO FOTOGRAFÍA...`, id: typingId });
    saveChatHistory();

    try {
        if (!apiService || !apiService.isTokenPresent()) {
            throw new Error("Acceso denegado: Se requiere autenticación para usar el Motor de Visión.");
        }

        const formData = new FormData();
        formData.append('image', file);
        const currentOp = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
        formData.append('operator', currentOp);

        const data = await apiService.upload('vision/analyze/', formData);

        const typingElement = document.getElementById(typingId);
        if (typingElement) typingElement.remove();

        const serverReply = `
**DIAGNÓSTICO VISUAL CNN:**
- **ESPECIE:** ${data.species || 'DESCONOCIDA'}
- **CONDICIÓN:** ${data.condition || 'NO DETECTADA'}
- **SEVERIDAD:** ${data.severity ? data.severity.toUpperCase() : 'N/A'}
- **PH ESTIMADO:** ${data.ph_predicted !== null && data.ph_predicted !== undefined ? data.ph_predicted : 'N/A'}
- **CONFIANZA:** ${data.confidence ? (data.confidence * 100).toFixed(1) + '%' : 'N/A'}
        `.trim();

        chatMessagesData.push({ type: 'bot', text: serverReply });
        appendMessage(chatMessagesData[chatMessagesData.length - 1]);

        if (data.severity && data.severity.toLowerCase() === 'high' && typeof window.logPlantIssue === 'function') {
            window.logPlantIssue(data.species || "ESPECIE", data.condition);
        }

    } catch (error) {
        console.error("Error en motor de visión del chat:", error);
        if (error && error.status === 401) {
            apiService.clearToken();
            window.location.href = '/login.html';
            return;
        }

        const typingElement = document.getElementById(typingId);
        if (typingElement) typingElement.remove();
        
        const errorMsg = error.data?.detail?.title || error.message || "Motor de Visión Inaccesible";
        const errorText = `> ERROR: ${errorMsg}`;
        chatMessagesData.push({ type: 'error', text: errorText });
        appendMessage(chatMessagesData[chatMessagesData.length - 1]);
    }

    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
    saveChatHistory();
}