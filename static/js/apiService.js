/**
 * API Service - Wrapper para fetch con autenticación Supabase
 * Maneja todas las comunicaciones con el backend Django
 */

class ApiService {
    constructor(baseUrl = 'http://127.0.0.1:8000/api/v1/', supabaseClient = null) {
        // Asegura que la URL base termine en /
        this.baseUrl = baseUrl.endsWith('/') ? baseUrl : baseUrl + '/';
        this.supabase = supabaseClient;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };
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
    async buildHeaders(additionalHeaders = {}) {
        const headers = { ...this.defaultHeaders, ...additionalHeaders };

        const token = await this.getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
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
            const errorMessage = (data && data.message) ? data.message : `Error HTTP ${response.status}`;
            const error = new Error(errorMessage);
            error.status = response.status;
            error.data = data;
            
            // Lógica específica por código de estado
            if (response.status === 401 && this.supabase) {
                console.warn('Sesión expirada o inválida');
                // Opcional: await this.supabase.auth.signOut();
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
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/`;
        
        console.log('Conectando WebSocket a Mole-AI:', wsUrl);
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
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
                
                // Intentar reconexión automática (máximo 5 intentos)
                if (this.wsReconnectAttempts < 5) {
                    this.wsReconnectAttempts = (this.wsReconnectAttempts || 0) + 1;
                    console.log(`🔄 Intentando reconectar (${this.wsReconnectAttempts}/5)...`);
                    setTimeout(() => this.initWebSocket(), 3000);
                }
            };
            
        } catch (error) {
            console.error('Error creando WebSocket:', error);
            this.wsConnected = false;
        }
    }

    /**
     * Enviar mensaje de chat a través de WebSocket
     */
    sendChatMessage(question, plantId = null) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            console.log('WebSocket no conectado, inicializando...');
            this.initWebSocket();
            
            // Esperar a que se conecte y luego enviar
            const checkConnection = setInterval(() => {
                if (this.wsConnected) {
                    clearInterval(checkConnection);
                    this._doSendChatMessage(question, plantId);
                }
            }, 100);
            
            // Timeout después de 10 segundos
            setTimeout(() => clearInterval(checkConnection), 10000);
        } else {
            this._doSendChatMessage(question, plantId);
        }
    }

    /**
     * Método interno para enviar mensaje WebSocket
     */
    _doSendChatMessage(question, plantId) {
        const message = {
            question: question,
            plant_id: plantId
        };
        
        this.websocket.send(JSON.stringify(message));
        console.log('📤 Mensaje enviado a Mole-AI:', message);
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