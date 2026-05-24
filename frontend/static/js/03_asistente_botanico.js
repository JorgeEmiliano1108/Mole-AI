// ==========================================================
// 3. ASISTENTE BOTÁNICO (SISTEMA MULTI-MODELO) - 100% FUNCIONAL
// ==========================================================

// Definición de los 3 Motores de IA (Cerebros)
const IA_ENGINES = {
    CHAT: 'conversational-botanist', // IA de texto y consejos
    VISION: 'vision-analyzer',       // IA para diagnóstico por foto (Módulo 8)
    STATS: 'statistical-expert'      // IA para análisis de gráficas y sensores (Módulo 4)
};

/**
 * Crea una burbuja de bot con avatar (100% Anti-XSS)
 */
function _createBotBubble(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-bubble-bot';

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'bot-avatar';
    const avatarImg = document.createElement('img');
    avatarImg.src = '/static/assets/mole_tech_fab.png';
    avatarImg.alt = 'MOLE';
    avatarImg.style.cssText = 'width:100%;height:100%;object-fit:cover;';
    avatarDiv.appendChild(avatarImg);
    wrapper.appendChild(avatarDiv);

    const inner = document.createElement('div');
    inner.className = 'bubble-inner';
    inner.textContent = text;
    wrapper.appendChild(inner);

    return wrapper;
}

/**
 * Crea el separador de fecha "HOY"
 */
function _createDateSeparator(label = 'HOY') {
    const sep = document.createElement('div');
    sep.className = 'chat-date-separator';
    const span = document.createElement('span');
    span.textContent = label;
    sep.appendChild(span);
    return sep;
}

/**
 * CARGA DE HISTORIAL: Recupera la conversación del almacenamiento local.
 */
function loadChatHistory() {
    const chatBox = document.getElementById('chat-messages');
    if (!chatBox) return;

    const savedChat = localStorage.getItem('moleia_chat_history');
    if (savedChat) {
        chatBox.innerHTML = savedChat;
    } else {
        chatBox.textContent = '';
        chatBox.appendChild(_createDateSeparator('HOY'));
        chatBox.appendChild(_createBotBubble('¡Hola! Soy tu asistente MOLE-AI. ¿Cómo puedo ayudarte a optimizar tu cultivo hoy?'));
    }
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
 * Crea el indicador de escritura (typing dots) con el nuevo estilo
 */
function _createTypingIndicator(id) {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-bubble-bot typing-indicator';
    wrapper.id = id;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'bot-avatar';
    const avatarImg = document.createElement('img');
    avatarImg.src = '/static/assets/mole_tech_fab.png';
    avatarImg.alt = 'MOLE';
    avatarImg.style.cssText = 'width:100%;height:100%;object-fit:cover;';
    avatarDiv.appendChild(avatarImg);
    wrapper.appendChild(avatarDiv);

    const inner = document.createElement('div');
    inner.className = 'bubble-inner';
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'dot';
        inner.appendChild(dot);
    }
    wrapper.appendChild(inner);
    return wrapper;
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

    // Ocultar acciones sugeridas al empezar a chatear
    const suggestedActions = document.getElementById('chat-suggested-actions');
    if (suggestedActions) suggestedActions.style.display = 'none';

    if (!customPrompt) {
        // Burbuja del usuario (derecha, verde)
        const userWrapper = document.createElement('div');
        userWrapper.className = 'chat-bubble-user';
        const userInner = document.createElement('div');
        userInner.className = 'bubble-inner';
        userInner.textContent = query;
        userWrapper.appendChild(userInner);
        chatMessages.appendChild(userWrapper);
        input.value = '';
    }

    // Typing indicator (puntos animados)
    const typingId = 'typing-' + Date.now();
    const typingEl = _createTypingIndicator(typingId);
    chatMessages.appendChild(typingEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    saveChatHistory(); 

    try {
        // 🚀 USO DE API SERVICE
        const data = await window.moleApi.post('chat/', {
            prompt: query,
            engine: engine,
            sessionId: localStorage.getItem('moleia_current_user') || 'anon'
        });
        
        const typingElement = document.getElementById(typingId);
        if (typingElement) typingElement.remove();

        const serverReply = data.answer || data.reply || data.response || 'Análisis completado.';
        
        // Burbuja de respuesta del bot (izquierda, gris)
        const botWrapper = document.createElement('div');
        botWrapper.className = 'chat-bubble-bot';

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'bot-avatar';
        const avatarImg = document.createElement('img');
        avatarImg.src = '/static/assets/mole_tech_fab.png';
        avatarImg.alt = 'MOLE';
        avatarImg.style.cssText = 'width:100%;height:100%;object-fit:cover;';
        avatarDiv.appendChild(avatarImg);
        botWrapper.appendChild(avatarDiv);

        const inner = document.createElement('div');
        inner.className = 'bubble-inner';
        inner.textContent = serverReply;
        botWrapper.appendChild(inner);
        chatMessages.appendChild(botWrapper);
        
        // Disparamos evento si trae disclaimer médico (COFEPRIS Fase 3)
        if (data.disclaimer) {
            window.dispatchEvent(new CustomEvent('disclaimerReceived', { detail: { text: data.disclaimer } }));
        }

    } catch (error) {
        document.getElementById(typingId)?.remove();
        const errWrapper = document.createElement('div');
        errWrapper.className = 'chat-bubble-bot';
        const errAvatar = document.createElement('div');
        errAvatar.className = 'bot-avatar';
        const errImg = document.createElement('img');
        errImg.src = '/static/assets/topo.png';
        errImg.style.cssText = 'width:100%;height:100%;object-fit:cover;';
        errAvatar.appendChild(errImg);
        errWrapper.appendChild(errAvatar);
        const errInner = document.createElement('div');
        errInner.className = 'bubble-inner';
        errInner.style.color = '#f87171';
        errInner.textContent = `⚠ Enlace con ${engine} interrumpido. Intenta de nuevo.`;
        errWrapper.appendChild(errInner);
        chatMessages.appendChild(errWrapper);
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