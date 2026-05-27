// ==========================================================
// 12. SEGURIDAD S1 Y RENDERIZADO DE CHAT IA [ESTRICTO / ANTI-XSS]
// ==========================================================

/**
 * 1. RENDERIZADO SEGURO: Inyecta mensajes del usuario o del sistema al chat.
 * Emplea textContent estrictamente para evitar inyecci n de c digo (XSS).
 */
export function appendChatMessage(containerId, role, text, opts = {}) {
    // Acepta tanto el ID en string como el elemento HTML directo
    const container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    if (!container) return null;

    const msg = document.createElement('div');
    msg.className = `ai-message ${role} flex flex-col gap-2 mb-4 ${opts.extraClass || ''}`;

    // Si trae imagen adjunta (ej. cuando el usuario sube la foto al chat)
    if (opts.withImage && opts.imageSrc) {
        const imgContainer = document.createElement('div');
        imgContainer.className = 'p-1 border border-[#00e5ff]/30 inline-block self-start bg-black/50';
        
        const img = document.createElement('img');
        img.className = 'w-32 h-32 object-cover opacity-80 hover:opacity-100 transition-opacity';
        img.alt = 'Evidencia escaneada';
        img.src = opts.imageSrc;
        
        imgContainer.appendChild(img);
        msg.appendChild(imgContainer);
    }

    // Estructura visual dependiendo si es usuario (operador) o sistema (IA)
    const wrapper = document.createElement('div');
    wrapper.className = role === 'user' 
        ? 'bg-[#00e5ff]/10 border border-[#00e5ff]/30 p-2 self-end max-w-[85%]' 
        : 'p-2 max-w-[95%] self-start';

    // Inyectamos el texto de forma segura (NUNCA innerHTML aqu )
    const textNode = document.createElement('div');
    textNode.className = `chat-text text-xs md:text-sm font-mono break-words ${role === 'user' ? 'text-white text-right' : 'text-white/80'}`;
    textNode.textContent = text || '';
    
    wrapper.appendChild(textNode);
    msg.appendChild(wrapper);
    container.appendChild(msg);
    
    // Auto-scroll t ctico hacia el fondo
    container.scrollTop = container.scrollHeight;
    return msg;
}

/**
 * 2. RENDERIZADO MULTIL NEA DEL MOTOR LLM: 
 * Procesa la respuesta de la IA l nea por l nea manteniendo el formato y la seguridad.
 */
export function appendMultilineBotMessage(containerId, answer, tacticalCount = 0) {
    const container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    if (!container) return null;

    const wrapper = document.createElement('div');
    wrapper.className = 'ai-message bot border-l-2 border-[#00e5ff] pl-3 mb-6 flex flex-col gap-1 max-w-[95%]';

    // Alerta t ctica (si el backend detect  anomal as cr ticas)
    if (tacticalCount > 0) {
        const badge = document.createElement('div');
        badge.className = 'text-red-500 font-bold border border-red-500 bg-red-500/10 px-2 py-1 text-[10px] tracking-widest mb-2 self-start uppercase animate-pulse';
        badge.textContent = `> ALERTA T\u00c1CTICA: ${tacticalCount} ANOMAL\u00cdA(S) DETECTADA(S)`;
        wrapper.appendChild(badge);
    }

    // Procesamos la respuesta de la IA (100% Anti-XSS)
    const lines = String(answer || '').split('\n');
    
    lines.forEach(line => {
        // Manejo de saltos de l nea vac os (doble enter de la IA)
        if (line.trim() === '') {
            const spacer = document.createElement('div');
            spacer.className = "h-2"; 
            wrapper.appendChild(spacer);
            return;
        }

        const p = document.createElement('p');
        p.textContent = line;
        p.className = "text-[#00e5ff] font-mono text-xs md:text-sm leading-relaxed";
        wrapper.appendChild(p);
    });

    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
    
    return wrapper;
}