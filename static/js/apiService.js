/**
 * API Service - Wrapper para fetch con autenticación Supabase
 * Maneja todas las comunicaciones con el backend Django
 */

class ApiService {
    constructor(baseUrl = null, supabaseClient = null) {
        // Resolve baseUrl from window.APP_CONFIG or fallback dynamic detection
        const detectedBase = (window.APP_CONFIG && window.APP_CONFIG.API_URL) || baseUrl || null;
        const hostname = window.location.hostname;
        const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
        const defaultLocal = 'http://127.0.0.1:8000/api/v1/';
        const defaultProd = '/api/v1/';

        const finalBase = detectedBase || (isLocal ? defaultLocal : defaultProd);

        // Ensure trailing slash
        this.baseUrl = finalBase.endsWith('/') ? finalBase : finalBase + '/';
        this.supabase = supabaseClient;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };

        // WebSocket fallback flag: when true, the client will send chat via HTTP POST
        this.useHttpFallback = false;
    }

    /**
     * Obtener token de autenticación de Supabase
     */
    async getAuthToken() {
        if (!this.supabase) return null;

        try {
            const { data, error } = await this.supabase.auth.getSession();
            if (error) throw error;
            return data.session?.access_token || null;
        } catch (error) {
            console.warn('Error obteniendo token:', error);
            return null;
        }
    }

    /**
     * Construir headers mezclando defaults + auth + custom
     */
    /**
     * Construir headers mezclando defaults + auth + custom
     */
    async buildHeaders(additionalHeaders = {}) {
        const headers = { ...this.defaultHeaders, ...additionalHeaders };

        const token = await this.getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    /**
     * Obtener headers de autenticación para uso externo
     */
    async getAuthHeaders() {
        return this.buildHeaders();
    }

    /**
     * Manejar la respuesta HTTP
     */
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        const isJson = contentType && contentType.includes('application/json');

        let data;

        try {
            if (isJson) {
                data = await response.json();
            } else {
                data = await response.text();
            }
        } catch (e) {
            data = null;
        }

        if (!response.ok) {
            // Crear un error personalizado
            const errorMessage = (data && data.detail) ? data.detail :
                ((data && data.message) ? data.message : `Error HTTP ${response.status}`);

            const error = new Error(errorMessage);
            error.status = response.status;
            error.data = data;

            // Lógica específica por código de estado
            if (response.status === 401) {
                console.warn('Sesión expirada o inválida (401)');
                // Si tenemos cliente Supabase, intentamos limpiar o refrescar?
                // Por ahora, asumimos que el Token expiró y forzamos logout lógica en el frontend
                // al propagar el error.
                if (this.supabase) {
                    // Opcional: intentar refresh si el cliente lo soporta transparentemente
                    // pero si llegamos aquí, es probable que ya sea inválido.
                    const { data: sessionData, error: sessionError } = await this.supabase.auth.getSession();
                    if (!sessionData?.session) {
                        // Realmente no hay sesión válida
                    }
                }
            }

            throw error;
        }

        return data;
    }

    /**
     * Método principal REQUEST
     */
    async request(endpoint, method = 'GET', body = null, customHeaders = {}) {
        // Limpiar endpoint para evitar dobles slashes (ej: base/ + /ruta)
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
        const url = `${this.baseUrl}${cleanEndpoint}`;

        // Determinar si debemos enviar token (Guard)
        const token = await this.getAuthToken();
        if (!token && !endpoint.includes('sensor-data')) {
            // Si es una ruta protegida y no hay token, ¿debemos abortar?
            // Dejamos pasar sensor-data para modo público/demo
            // console.warn("Request sin token a endpoint:", endpoint);
        }

        // Preparar opciones
        const options = {
            method: method.toUpperCase(),
            headers: await this.buildHeaders(customHeaders)
        };

        // Manejo del Body
        if (body !== null && method !== 'GET' && method !== 'HEAD') {
            if (body instanceof FormData) {
                // CRUCIAL: Al enviar FormData, el navegador debe poner el Content-Type automáticamente
                // con el boundary correcto. Debemos borrarlo de nuestros defaults.
                delete options.headers['Content-Type'];
                options.body = body;
            } else {
                options.body = JSON.stringify(body);
            }
        }

        try {
            const response = await fetch(url, options);
            return await this.handleResponse(response);
        } catch (error) {
            console.error(`API Error [${method} ${endpoint}]:`, error);
            throw error;
        }
    }

    // --- Métodos Helper ---

    get(endpoint) {
        return this.request(endpoint, 'GET');
    }

    post(endpoint, body) {
        return this.request(endpoint, 'POST', body);
    }

    put(endpoint, body) {
        return this.request(endpoint, 'PUT', body);
    }

    delete(endpoint) {
        return this.request(endpoint, 'DELETE');
    }

    // Helper específico para subir archivos
    upload(endpoint, formData) {
        return this.request(endpoint, 'POST', formData);
    }

    // --- WEBSOCKET METHODS FOR MOLE-AI CHAT ---

    /**
     * Inicializar conexión WebSocket para chat en tiempo real
     */
    initWebSocket() {
        // Cerrar conexión existente si hay una
        if (this.websocket) {
            this.websocket.close();
        }

        // Determinar protocolo WebSocket basado en HTTP/HTTPS
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        let wsUrl = `${protocol}//${window.location.host}/ws/chat/`;

        // BUILDER FIX: Inject Auth Token
        this.getAuthToken().then(token => {
            if (token) {
                // Encode token to handle special chars safe
                wsUrl += `?token=${encodeURIComponent(token)}`;
            } else {
                console.warn("Iniciando WebSocket sin token (Modo Anónimo)");
            }

            console.log('Conectando WebSocket a Mole-AI:', wsUrl);

            try {
                this.websocket = new WebSocket(wsUrl);
                this.useHttpFallback = false; // Reset fallback on new attempt
                this._setupWebSocketHandlers();
            } catch (e) {
                console.error('WebSocket init failed, enabling HTTP fallback', e);
                this.useHttpFallback = true;
            }
        });
    }

    _setupWebSocketHandlers() {
        if (!this.websocket) return;

        // Event handlers
        this.websocket.onopen = () => {
            console.log('✅ WebSocket conectado a Mole-AI');
            this.wsConnected = true;
            this.wsReconnectAttempts = 0;
            this.updateConnectionIndicator(true);
        };

        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error, event.data);
            }
        };

        this.websocket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.wsConnected = false;
            this.updateConnectionIndicator(false);
        };

        this.websocket.onclose = (event) => {
            console.log('🔌 WebSocket desconectado:', event.code, event.reason);
            this.wsConnected = false;
            this.updateConnectionIndicator(false);
            // In serverless platforms WebSocket may be closed; activate fallback
            this.useHttpFallback = true;

            // Intentar reconexión automática (máximo 5 intentos)
            // NO reconectar si el código es 4004 (Auth fallida) o similar 1006 repetitivo
            if (event.code !== 1000 && event.code !== 1001 && this.wsReconnectAttempts < 5) {
                // Exponential backoff
                const delay = Math.min(1000 * (2 ** this.wsReconnectAttempts), 10000);
                this.wsReconnectAttempts = (this.wsReconnectAttempts || 0) + 1;
                console.log(`🔄 Intentando reconectar en ${delay}ms (${this.wsReconnectAttempts}/5)...`);
                setTimeout(() => this.initWebSocket(), delay);
            }
        };
    }

    /**
     * Enviar mensaje de chat a través de WebSocket
     */
    sendChatMessage(question, plantId = null, imageBase64 = null) {
        // If HTTP fallback is enabled, send via HTTP immediately
        if (this.useHttpFallback) {
            console.warn('Using HTTP fallback for chat (WebSocket disabled)');
            this._sendChatViaHttp(question, plantId, imageBase64);
            return;
        }

        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            console.log('WebSocket no conectado, inicializando...');
            if (!this.websocket || this.websocket.readyState === WebSocket.CLOSED) {
                this.initWebSocket();
            }

            // Esperar a que readyState sea OPEN antes de enviar
            const checkConnection = setInterval(() => {
                if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                    clearInterval(checkConnection);
                    this._doSendChatMessage(question, plantId, imageBase64);
                }
            }, 150);

            // Timeout después de 10 segundos
            setTimeout(() => {
                clearInterval(checkConnection);
                if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
                    console.error('❌ Timeout esperando conexión WebSocket — usando fallback HTTP');
                    this.useHttpFallback = true;
                    this._sendChatViaHttp(question, plantId, imageBase64);
                }
            }, 10000);
        } else {
            this._doSendChatMessage(question, plantId, imageBase64);
        }
    }

    /**
     * Fallback: enviar chat vía HTTP POST al endpoint del backend
     */
    async _sendChatViaHttp(question, plantId = null, imageBase64 = null) {
        try {
            const payload = {
                question: question,
                plant_id: plantId
            };
            if (imageBase64) payload.image_base64 = imageBase64;

            // El endpoint espera JSON en: /api/v1/chat/fallback/
            const res = await this.post('chat/fallback/', payload);

            // Emitir evento con la respuesta para que el UI lo procese igual que WS
            window.dispatchEvent(new CustomEvent('chatMessage', { detail: res }));
        } catch (err) {
            console.error('Error sending chat via HTTP fallback:', err);
            window.dispatchEvent(new CustomEvent('chatMessage', {
                detail: { type: 'error', message: '❌ Falla de fallback HTTP: ' + (err.message || err) }
            }));
        }
    }

    /**
     * Método interno para enviar mensaje WebSocket
     */
    _doSendChatMessage(question, plantId, imageBase64 = null) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            console.warn('⚠️ WebSocket no está OPEN, reintentando...');
            this.sendChatMessage(question, plantId, imageBase64);
            return;
        }

        const message = {
            question: question,
            plant_id: plantId
        };

        // Adjuntar imagen si existe
        if (imageBase64) {
            message.image_base64 = imageBase64;
        }

        this.websocket.send(JSON.stringify(message));
        console.log('📤 Mensaje enviado a Mole-AI:', { question, plant_id: plantId, has_image: !!imageBase64 });
    }

    /**
     * Manejar mensajes recibidos del WebSocket
     */
    handleWebSocketMessage(data) {
        console.log('📥 Mensaje recibido de Mole-AI:', data);

        // Disparar evento personalizado para que el UI lo maneje
        window.dispatchEvent(new CustomEvent('chatMessage', {
            detail: data
        }));
    }

    /**
     * Verificar estado de conexión WebSocket
     */
    isWebSocketConnected() {
        return this.wsConnected && this.websocket && this.websocket.readyState === WebSocket.OPEN;
    }

    /**
     * Cerrar conexión WebSocket manualmente
     */
    closeWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
            this.wsConnected = false;
            this.updateConnectionIndicator(false);
        }
    }

    /**
     * Actualizar indicador visual de conexión
     */
    updateConnectionIndicator(connected) {
        const indicator = document.getElementById('websocket-indicator');
        if (indicator) {
            if (connected) {
                indicator.className = 'websocket-indicator connected';
                indicator.textContent = '🟢 Online';
            } else {
                indicator.className = 'websocket-indicator disconnected';
                indicator.textContent = '🔴 Offline';
            }
        }
    }
}

// Asignar a window para que esté disponible globalmente sin 'import'
window.ApiService = ApiService;