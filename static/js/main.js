// =============================================================================
// main.js — Mole-AI Terminal Frontend (Security-Hardened)
// ─────────────────────────────────────────────────────────
// • Removed all localStorage password/auth logic (Supabase-only auth)
// • Chat message handling with loading spinner
// • Toast notification rendering
// • COFEPRIS disclaimer banner
// • Daylight-override toggle
// =============================================================================

(function () {
    'use strict';

    // ─── INTRO DATA (typewriter) ────────────────────────────────────────

    const introData = {
        'objetivo': "> OBJETIVO:\n\nEstablecer un sistema de monitoreo biométrico continuo para la preservación de especies vegetales.",
        'vision': "> VISIÓN:\n\nCrear el banco de datos botánico más resistente del yermo.",
        'flora': "> FLORA MEXICANA:\n\nCatálogo de especímenes recuperados en cuarentena hidro-botánica.",
        'acerca': "> ACERCA DE LA WEB:\n\nTerminal MOLE-IA versión 2.0.0\nSistema Seguro, Encriptado y Multi-Rol.\nAuth: Supabase JWT | Zero Trust Gateway"
    };

    let typeInterval;

    // ─── TYPEWRITER EFFECT ──────────────────────────────────────────────

    window.typeContent = function (section) {
        const output = document.getElementById('typewriter-output');
        if (!output) return;
        const text = introData[section];
        if (!text) return;

        output.innerHTML = '';
        clearInterval(typeInterval);
        let currentText = '', i = 0;

        typeInterval = setInterval(() => {
            currentText += text.charAt(i);
            output.innerHTML = currentText + '<span class="animate-pulse">_</span>';
            i++;
            if (i === text.length) clearInterval(typeInterval);
        }, 20);
    };

    // ─── SCREEN NAVIGATION ──────────────────────────────────────────────

    window.startSystem = function () {
        const intro = document.getElementById('intro-screen');
        if (intro) intro.classList.add('hidden');
        clearInterval(typeInterval);
    };

    // ─── CHAT ───────────────────────────────────────────────────────────

    window.sendChatMessage = function () {
        const input = document.getElementById('chat-input');
        const chatOutput = document.getElementById('chat-output');
        if (!input || !chatOutput) return;

        const question = input.value.trim();
        if (!question) return;

        // Render user message
        const userMsg = document.createElement('div');
        userMsg.className = 'chat-msg chat-msg--user';
        userMsg.textContent = `> ${question}`;
        chatOutput.appendChild(userMsg);

        // Show loading spinner
        const loader = document.createElement('div');
        loader.className = 'chat-msg chat-msg--loading';
        loader.id = 'chat-loader';
        loader.setAttribute('role', 'status');
        loader.setAttribute('aria-label', 'Procesando respuesta');
        loader.innerHTML = '<span class="terminal-spinner"></span> Procesando...';
        chatOutput.appendChild(loader);

        input.value = '';
        chatOutput.scrollTop = chatOutput.scrollHeight;

        // Send via ApiService (try WebSocket first, fallback to HTTP)
        const api = window.moleApi;
        if (api) {
            if (api.isWebSocketConnected()) {
                api.sendChatMessage(question);
            } else {
                // HTTP fallback
                api.post('chat/fallback/', { question })
                    .then(data => {
                        _removeChatLoader();
                        _renderBotMessage(data.answer || data.response || 'Sin respuesta.');
                    })
                    .catch(() => {
                        _removeChatLoader();
                        _renderBotMessage('[ ERROR ] No se pudo procesar la solicitud.');
                    });
            }
        }
    };

    function _removeChatLoader() {
        const loader = document.getElementById('chat-loader');
        if (loader) loader.remove();
    }

    function _renderBotMessage(text) {
        const chatOutput = document.getElementById('chat-output');
        if (!chatOutput) return;
        const botMsg = document.createElement('div');
        botMsg.className = 'chat-msg chat-msg--bot';
        botMsg.textContent = `< ${text}`;
        chatOutput.appendChild(botMsg);
        chatOutput.scrollTop = chatOutput.scrollHeight;
    }

    // ─── WEBSOCKET MESSAGE LISTENER ─────────────────────────────────────

    window.addEventListener('chatMessage', (e) => {
        _removeChatLoader();
        const data = e.detail;
        _renderBotMessage(data.answer || data.response || data.message || 'Sin respuesta.');
    });

    // ─── COFEPRIS DISCLAIMER ────────────────────────────────────────────

    window.addEventListener('disclaimerReceived', (e) => {
        const container = document.getElementById('disclaimer-container');
        if (!container) return;

        container.innerHTML = `
            <div class="disclaimer-banner" role="alert">
                <div class="disclaimer-header">[ ALERTA LEGAL DEL SISTEMA ]</div>
                <div class="disclaimer-body">${_escapeHtml(e.detail.text)}</div>
                <button class="disclaimer-dismiss" aria-label="Cerrar alerta legal"
                        onclick="this.closest('.disclaimer-banner').remove()">
                    [ CERRAR ]
                </button>
            </div>
        `;
        container.classList.remove('hidden');
    });

    function _escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ─── DAYLIGHT OVERRIDE TOGGLE ───────────────────────────────────────

    window.toggleDaylightMode = function () {
        document.body.classList.toggle('daylight-override');
        const btn = document.getElementById('daylight-toggle-btn');
        if (btn) {
            const isActive = document.body.classList.contains('daylight-override');
            btn.textContent = isActive ? '[ MODO NOCTURNO ]' : '[ MODO LUZ SOLAR ]';
            btn.setAttribute('aria-pressed', String(isActive));
        }
    };

    // ─── INIT ON DOM READY ──────────────────────────────────────────────

    document.addEventListener('DOMContentLoaded', () => {
        // Initialize ApiService (Supabase client can be attached later)
        try {
            window.moleApi = new window.ApiService();
        } catch (err) {
            console.error('[main] No se pudo inicializar ApiService:', err.message);
        }

        // Chat input Enter key
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') window.sendChatMessage();
            });
        }

        // Initialize WebSocket connection
        if (window.moleApi) {
            window.moleApi.initWebSocket();
        }
    });

})();
