/**
 * API Service — Zero Trust HTTP Gateway + WebSocket
 * ─────────────────────────────────────────────────
 * • No hardcoded URLs — reads from window.APP_CONFIG only
 * • AbortController timeouts (30s default, 120s AI)
 * • Exponential backoff retry (max 3 for network errors)
 * • Friendly Spanish error messages for field conditions
 * • COFEPRIS disclaimer detection + event dispatch
 * • Toast notification utility
 * • Loading state management
 */

class ApiService {
    constructor(supabaseClient = null) {
        'use strict';

        const cfg = window.APP_CONFIG;
        if (!cfg || !cfg.API_URL) {
            throw new Error('[ApiService] window.APP_CONFIG.API_URL no definido.');
        }

        this.baseUrl = cfg.API_URL.endsWith('/') ? cfg.API_URL : cfg.API_URL + '/';
        this.supabase = supabaseClient;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };

        // Timeout config
        this.defaultTimeout = cfg.TIMEOUTS?.DEFAULT || 30000;
        this.aiTimeout = cfg.TIMEOUTS?.AI || 120000;

        // Retry config
        this.maxRetries = cfg.RETRY?.MAX_ATTEMPTS || 3;
        this.retryBaseDelay = cfg.RETRY?.BASE_DELAY || 1000;

        // AI endpoints that get longer timeouts
        this._aiEndpoints = ['chat', 'diagnostic', 'llm', 'vision', 'rag'];

        // WebSocket state
        this.websocket = null;
        this.wsConnected = false;
        this.wsReconnectAttempts = 0;
    }

    // ─── AUTH ────────────────────────────────────────────────────────────

    async getAuthToken() {
        if (!this.supabase) return null;
        try {
            const { data, error } = await this.supabase.auth.getSession();
            if (error) throw error;
            return data.session?.access_token || null;
        } catch (err) {
            console.warn('[ApiService] Error obteniendo token:', err.message);
            return null;
        }
    }

    async buildHeaders(additionalHeaders = {}) {
        const headers = { ...this.defaultHeaders, ...additionalHeaders };
        const token = await this.getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    }

    // ─── TIMEOUT HELPER ─────────────────────────────────────────────────

    _getTimeout(endpoint) {
        const ep = endpoint.toLowerCase();
        return this._aiEndpoints.some(ai => ep.includes(ai))
            ? this.aiTimeout
            : this.defaultTimeout;
    }

    // ─── RESPONSE HANDLER ───────────────────────────────────────────────

    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        const isJson = contentType && contentType.includes('application/json');

        let data;
        try {
            data = isJson ? await response.json() : await response.text();
        } catch (_) {
            data = null;
        }

        // ── COFEPRIS Disclaimer detection ──
        if (isJson && data && typeof data === 'object' && data.disclaimer) {
            window.dispatchEvent(new CustomEvent('disclaimerReceived', {
                detail: { text: data.disclaimer }
            }));
        }

        if (!response.ok) {
            const errorMessage = (data && data.message) ? data.message : `Error HTTP ${response.status}`;
            const error = new Error(errorMessage);
            error.status = response.status;
            error.data = data;

            // Session expired
            if (response.status === 401 && this.supabase) {
                console.warn('[ApiService] Sesión expirada o inválida');
            }

            throw error;
        }

        return data;
    }

    // ─── FRIENDLY ERROR MESSAGES ────────────────────────────────────────

    _friendlyMessage(error) {
        if (error instanceof TypeError) {
            // Network error (offline, DNS, CORS preflight failure)
            return 'Sin conexión a internet. Verifica tu señal.';
        }
        if (error.name === 'AbortError') {
            return 'La conexión en el campo es inestable. Reintentando...';
        }
        const s = error.status;
        if (s === 503) return 'El servicio de IA está procesando. Intenta en unos segundos.';
        if (s === 504) return 'La conexión en el campo es inestable. Reintentando...';
        if (s === 429) return 'Demasiadas solicitudes. Espera un momento.';
        if (s === 401) return 'Sesión expirada. Vuelve a iniciar sesión.';
        if (s >= 500) return 'Error interno del servidor. Intenta más tarde.';
        return error.message || 'Error desconocido.';
    }

    // ─── REQUEST WITH RETRY + TIMEOUT ───────────────────────────────────

    async request(endpoint, method = 'GET', body = null, customHeaders = {}) {
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
        const url = `${this.baseUrl}${cleanEndpoint}`;
        const timeout = this._getTimeout(cleanEndpoint);

        let lastError = null;

        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), timeout);

            try {
                const options = {
                    method: method.toUpperCase(),
                    headers: await this.buildHeaders(customHeaders),
                    signal: controller.signal,
                };

                // Body handling
                if (body !== null && method !== 'GET' && method !== 'HEAD') {
                    if (body instanceof FormData) {
                        delete options.headers['Content-Type'];
                        options.body = body;
                    } else {
                        options.body = JSON.stringify(body);
                    }
                }

                const response = await fetch(url, options);
                clearTimeout(timer);
                return await this.handleResponse(response);

            } catch (error) {
                clearTimeout(timer);
                lastError = error;

                // Only retry on network errors or timeouts, not HTTP errors
                const isRetryable = (error instanceof TypeError) || (error.name === 'AbortError');

                if (!isRetryable || attempt >= this.maxRetries) {
                    break;
                }

                // Exponential backoff: 1s, 2s, 4s
                const delay = this.retryBaseDelay * Math.pow(2, attempt);
                console.warn(`[ApiService] Retry ${attempt + 1}/${this.maxRetries} en ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }

        // All retries exhausted
        const friendlyMsg = this._friendlyMessage(lastError);
        ApiService.showToast(friendlyMsg, 'error');
        console.error(`[ApiService] ${method} ${endpoint} falló:`, lastError);
        throw lastError;
    }

    // ─── HELPER METHODS ─────────────────────────────────────────────────

    get(endpoint) { return this.request(endpoint, 'GET'); }
    post(endpoint, body) { return this.request(endpoint, 'POST', body); }
    put(endpoint, body) { return this.request(endpoint, 'PUT', body); }
    delete(endpoint) { return this.request(endpoint, 'DELETE'); }
    upload(endpoint, formData) { return this.request(endpoint, 'POST', formData); }

    // ─── TOAST NOTIFICATIONS (Terminal Style) ───────────────────────────

    static showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const prefixes = {
            error: '[ ERROR ]',
            warn: '[ WARN  ]',
            info: '[ INFO  ]',
            success: '[ OK    ]'
        };
        const prefix = prefixes[type] || prefixes.info;

        const toast = document.createElement('div');
        toast.className = `terminal-toast terminal-toast--${type}`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `<span class="toast-prefix">${prefix}</span> ${message}`;

        container.appendChild(toast);

        // Auto-remove after 6s
        setTimeout(() => {
            toast.classList.add('toast-fade-out');
            setTimeout(() => toast.remove(), 400);
        }, 6000);
    }

    // ─── LOADING STATE ──────────────────────────────────────────────────

    static setLoading(elementId, isLoading) {
        const el = document.getElementById(elementId);
        if (!el) return;
        if (isLoading) {
            el.classList.add('is-loading');
            el.setAttribute('aria-busy', 'true');
        } else {
            el.classList.remove('is-loading');
            el.removeAttribute('aria-busy');
        }
    }

    // ─── WEBSOCKET ──────────────────────────────────────────────────────

    initWebSocket() {
        if (this.websocket) {
            this.websocket.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/`;

        try {
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                this.wsConnected = true;
                this.wsReconnectAttempts = 0;
                this.updateConnectionIndicator(true);
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (err) {
                    console.error('[WS] Error parsing message:', err);
                }
            };

            this.websocket.onerror = () => {
                this.wsConnected = false;
                this.updateConnectionIndicator(false);
            };

            this.websocket.onclose = (event) => {
                this.wsConnected = false;
                this.updateConnectionIndicator(false);

                if (this.wsReconnectAttempts < 5) {
                    this.wsReconnectAttempts = (this.wsReconnectAttempts || 0) + 1;
                    const delay = 3000 * this.wsReconnectAttempts;
                    setTimeout(() => this.initWebSocket(), delay);
                }
            };

        } catch (err) {
            console.error('[WS] Error creando WebSocket:', err);
            this.wsConnected = false;
        }
    }

    sendChatMessage(question, plantId = null) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            this.initWebSocket();
            const checkConnection = setInterval(() => {
                if (this.wsConnected) {
                    clearInterval(checkConnection);
                    this._doSendChatMessage(question, plantId);
                }
            }, 100);
            setTimeout(() => {
                clearInterval(checkConnection);
                if (!this.wsConnected) {
                    ApiService.showToast('Sin conexión a internet. Verifica tu señal.', 'error');
                }
            }, 10000);
        } else {
            this._doSendChatMessage(question, plantId);
        }
    }

    _doSendChatMessage(question, plantId) {
        const message = { question, plant_id: plantId };
        this.websocket.send(JSON.stringify(message));
    }

    handleWebSocketMessage(data) {
        // COFEPRIS Disclaimer detection in WS messages
        if (data && data.disclaimer) {
            window.dispatchEvent(new CustomEvent('disclaimerReceived', {
                detail: { text: data.disclaimer }
            }));
        }

        window.dispatchEvent(new CustomEvent('chatMessage', { detail: data }));
    }

    isWebSocketConnected() {
        return this.wsConnected && this.websocket && this.websocket.readyState === WebSocket.OPEN;
    }

    closeWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
            this.wsConnected = false;
            this.updateConnectionIndicator(false);
        }
    }

    updateConnectionIndicator(connected) {
        const indicator = document.getElementById('websocket-indicator');
        if (!indicator) return;
        if (connected) {
            indicator.className = 'websocket-indicator connected';
            indicator.textContent = '■ ONLINE';
        } else {
            indicator.className = 'websocket-indicator disconnected';
            indicator.textContent = '■ OFFLINE';
        }
    }
}

// Global export (no ES modules)
window.ApiService = ApiService;