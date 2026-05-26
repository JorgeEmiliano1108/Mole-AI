// ==========================================================
// 12. SEGURIDAD S1 Y RENDERIZADO DE CHAT IA [ESTRICTO / ANTI-XSS]
// ==========================================================

/**
 * 1. RENDERIZADO SEGURO: Inyecta mensajes del usuario o del sistema al chat.
 * Emplea textContent estrictamente para evitar inyección de código (XSS).
 * Nuevo diseño: burbujas modernas — usuario (derecha/verde) | bot (izquierda/gris)
 */
function appendChatMessage(containerId, role, text, opts = {}) {
    const container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    if (!container) return null;

    const wrapper = document.createElement('div');

    if (role === 'user') {
        wrapper.className = 'chat-bubble-user';
        const inner = document.createElement('div');
        inner.className = 'bubble-inner';
        inner.textContent = text || '';
        wrapper.appendChild(inner);
    } else {
        wrapper.className = 'chat-bubble-bot';

        // Avatar miniatura del bot
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'bot-avatar';
        const avatarImg = document.createElement('img');
        avatarImg.src = '/static/assets/mole_tech_fab.png';
        avatarImg.alt = 'MOLE';
        avatarImg.style.cssText = 'width:100%;height:100%;object-fit:cover;';
        avatarDiv.appendChild(avatarImg);
        wrapper.appendChild(avatarDiv);

        // Burbuja de texto
        const inner = document.createElement('div');
        inner.className = `bubble-inner ${opts.extraClass || ''}`;

        // Si trae imagen adjunta (ej. cuando el usuario sube la foto)
        if (opts.withImage && opts.imageSrc) {
            const img = document.createElement('img');
            img.className = 'w-32 h-32 object-cover rounded-lg mb-2 opacity-90';
            img.alt = 'Evidencia escaneada';
            img.src = opts.imageSrc;
            inner.appendChild(img);
        }

        const textNode = document.createElement('span');
        textNode.textContent = text || '';
        inner.appendChild(textNode);
        wrapper.appendChild(inner);
    }

    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
    return wrapper;
}

/**
 * 2. RENDERIZADO MULTILÍNEA DEL MOTOR LLM: 
 * Procesa la respuesta de la IA línea por línea manteniendo el formato y la seguridad.
 * Usa burbuja bot con avatar y estilo moderno.
 */
function appendMultilineBotMessage(containerId, answer, tacticalCount = 0) {
    const container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    if (!container) return null;

    const wrapper = document.createElement('div');
    wrapper.className = 'chat-bubble-bot';

    // Avatar miniatura del bot
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'bot-avatar';
    avatarDiv.style.cssText = 'align-self:flex-start;margin-top:4px;';
    const avatarImg = document.createElement('img');
    avatarImg.src = '/static/assets/topo.png';
    avatarImg.alt = 'MOLE';
    avatarImg.style.cssText = 'width:100%;height:100%;object-fit:cover;';
    avatarDiv.appendChild(avatarImg);
    wrapper.appendChild(avatarDiv);

    const bubble = document.createElement('div');
    bubble.className = 'bubble-inner';

    // Alerta táctica (si el backend detectó anomalías críticas)
    if (tacticalCount > 0) {
        const badge = document.createElement('div');
        badge.style.cssText = 'color:#f87171;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.4);padding:4px 10px;border-radius:8px;font-size:11px;font-weight:700;margin-bottom:8px;letter-spacing:0.05em;text-transform:uppercase;';
        badge.textContent = `⚠ ALERTA TÁCTICA: ${tacticalCount} ANOMALÍA(S) DETECTADA(S)`;
        bubble.appendChild(badge);
    }

    // Procesamos la respuesta de la IA (100% Anti-XSS)
    const lines = String(answer || '').split('\n');
    lines.forEach(line => {
        if (line.trim() === '') {
            const spacer = document.createElement('div');
            spacer.style.height = '6px';
            bubble.appendChild(spacer);
            return;
        }
        const p = document.createElement('p');
        p.textContent = line;
        p.style.cssText = 'margin:0;line-height:1.6;';
        bubble.appendChild(p);
    });

    wrapper.appendChild(bubble);
    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
    return wrapper;
}