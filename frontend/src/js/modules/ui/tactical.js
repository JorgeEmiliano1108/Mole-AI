/**
 * tactical.js — Mole.AI Frontend Resilience Layer
 * ═══════════════════════════════════════════════════
 * Provides:
 *   1. showTacticalToast(msg, type) — styled error/warning/success toasts
 *   2. setConnectionStatus(state) — live WebSocket indicator management
 *   3. showInferenceState(targetId, label) / clearInferenceState(targetId) — loading states
 *
 * All UI follows the Cyber-Agrícola design system tokens.
 */

// ─── 1. TACTICAL TOAST NOTIFICATIONS ────────────────────────────────────────

const TOAST_COLORS = {
    error:   { border: '#F87171', bg: 'rgba(248,113,113,0.08)', text: '#F87171', prefix: '[ERROR]' },
    warn:    { border: '#FBBF24', bg: 'rgba(251,191,36,0.08)',  text: '#FBBF24', prefix: '[WARN]' },
    success: { border: '#34D399', bg: 'rgba(52,211,153,0.08)',  text: '#34D399', prefix: '[OK]' },
    info:    { border: '#00E5FF', bg: 'rgba(0,229,255,0.08)',   text: '#00E5FF', prefix: '[INFO]' },
};

/**
 * Render a tactical console-styled toast notification.
 * Auto-removes after `duration` ms (default 6000).
 */
export function showTacticalToast(message, type = 'error', duration = 6000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        // Create one if it doesn't exist on the current page
        container = document.createElement('div');
        container.id = 'toast-container';
        container.setAttribute('aria-live', 'polite');
        container.className = 'fixed top-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm';
        document.body.appendChild(container);
    }

    const palette = TOAST_COLORS[type] || TOAST_COLORS.info;

    const toast = document.createElement('div');
    toast.setAttribute('role', 'alert');
    toast.style.cssText = `
        border: 1px solid ${palette.border}40;
        background: ${palette.bg};
        color: ${palette.text};
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        padding: 10px 14px;
        border-radius: 6px;
        display: flex;
        align-items: flex-start;
        gap: 8px;
        opacity: 0;
        transform: translateX(20px);
        transition: opacity 0.3s, transform 0.3s;
        backdrop-filter: blur(8px);
        box-shadow: 0 0 15px ${palette.border}15;
    `;

    const prefix = document.createElement('span');
    prefix.style.fontWeight = '700';
    prefix.style.whiteSpace = 'nowrap';
    prefix.textContent = palette.prefix;

    const msg = document.createElement('span');
    msg.style.opacity = '0.85';
    msg.textContent = message;

    toast.appendChild(prefix);
    toast.appendChild(msg);
    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    });

    // Auto-remove
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ─── 2. WEBSOCKET CONNECTION INDICATOR ──────────────────────────────────────

const CONNECTION_STATES = {
    connected:    { color: '#34D399', label: 'LINK UP',          pulseClass: '' },
    reconnecting: { color: '#FBBF24', label: 'RECONNECTING...', pulseClass: 'animate-pulse' },
    disconnected: { color: '#F87171', label: 'LINK DOWN',        pulseClass: '' },
};

/**
 * Update the live connection indicator in the dashboard header.
 * Expects an element with id="ws-status-dot" and id="ws-status-label".
 */
export function setConnectionStatus(state) {
    const dot = document.getElementById('ws-status-dot');
    const label = document.getElementById('ws-status-label');
    if (!dot || !label) return;

    const cfg = CONNECTION_STATES[state] || CONNECTION_STATES.disconnected;
    dot.style.backgroundColor = cfg.color;
    dot.className = `w-2 h-2 rounded-full shrink-0 ${cfg.pulseClass}`;
    label.textContent = cfg.label;
    label.style.color = cfg.color;
}

/**
 * Attach WebSocket lifecycle hooks to the connection indicator.
 * Call this once after creating a WebSocket instance.
 *
 * @param {WebSocket} ws — The active WebSocket connection
 */
export function bindWebSocket(ws) {
    if (!ws) return;

    ws.addEventListener('open', () => {
        setConnectionStatus('connected');
        showTacticalToast('Enlace con el backend establecido.', 'success', 3000);
    });

    ws.addEventListener('close', () => {
        setConnectionStatus('disconnected');
        showTacticalToast('Conexión con el backend perdida. Datos congelados.', 'error');
    });

    ws.addEventListener('error', () => {
        setConnectionStatus('disconnected');
        showTacticalToast('Error de red en WebSocket. Reintentando...', 'warn');
    });
}

// ─── 3. INFERENCE / LOADING STATE MANAGEMENT ────────────────────────────────

/**
 * Show a pulsing "[INFERRING...]" or custom label inside a target DOM element.
 * Preserves existing content by storing it in a data attribute.
 *
 * @param {string} targetId — ID of the DOM element to show loading in
 * @param {string} label — Text to display (default: 'PROCESANDO...')
 */
export function showInferenceState(targetId, label = 'PROCESANDO...') {
    const el = document.getElementById(targetId);
    if (!el) return;

    // Store original content for restoration
    if (!el.dataset.originalContent) {
        el.dataset.originalContent = el.innerHTML;
    }

    el.innerHTML = `
        <div class="flex items-center gap-2 animate-pulse">
            <div class="flex gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-mole-cyan animate-bounce" style="animation-delay: 0ms"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-mole-cyan animate-bounce" style="animation-delay: 150ms"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-mole-cyan animate-bounce" style="animation-delay: 300ms"></span>
            </div>
            <span class="text-xs text-mole-cyan font-mono font-bold tracking-widest">[${label}]</span>
        </div>
    `;
}

/**
 * Clear the inference/loading state and restore original content.
 *
 * @param {string} targetId — ID of the DOM element to restore
 * @param {string|null} newContent — Optional new HTML to set instead of original
 */
export function clearInferenceState(targetId, newContent = null) {
    const el = document.getElementById(targetId);
    if (!el) return;

    if (newContent !== null) {
        el.innerHTML = newContent;
    } else if (el.dataset.originalContent) {
        el.innerHTML = el.dataset.originalContent;
    }
    delete el.dataset.originalContent;
}

// ─── GLOBAL EXPOSURE ────────────────────────────────────────────────────────
// Make available on window for non-module scripts (legacy compat)
window.showTacticalToast = showTacticalToast;
window.setConnectionStatus = setConnectionStatus;
window.bindWebSocket = bindWebSocket;
window.showInferenceState = showInferenceState;
window.clearInferenceState = clearInferenceState;
