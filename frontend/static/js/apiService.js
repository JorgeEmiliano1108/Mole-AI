/**
 * ApiService — Clean HTTP client for Mole-AI Django API Gateway
 * ──────────────────────────────────────────────────────────────
 * • Points to http://localhost:8000/api/v1/
 * • fetch-based with AbortController timeouts
 * • Exponential backoff retry for network errors
 * • FormData support (auto-drops Content-Type)
 * • COFEPRIS disclaimer detection + event dispatch
 * • Toast notification utility
 * • Spanish-friendly error messages
 */

class ApiService {

    constructor() {
        this.baseUrl = window.AppConfig ? window.AppConfig.API_BASE_URL : window.location.origin + '/api/v1/';
        this.defaultTimeout = 30000;   // 30s for standard requests
        this.aiTimeout = 120000;       // 120s for AI/LLM endpoints
        this.maxRetries = 3;
        this.retryBaseDelay = 1000;    // 1s base, exponential backoff
        this._aiEndpoints = ['chat', 'diagnostic', 'llm', 'vision', 'rag', 'cnn'];

        // Session token (set after login)
        this.authToken = null;
        // Authorization prefix (use Bearer to match backend LocalAuthentication)
        this.authPrefix = 'Bearer ';
    }

    // ─── AUTH TOKEN MANAGEMENT ──────────────────────────────────────────

    setToken(token) {
        return new Promise(resolve => {
            // Defensive: only accept non-empty string tokens
            if (typeof token !== 'string' || token.trim() === '') {
                console.warn('ApiService.setToken: invalid token received, refusing to persist.');
                // Ensure we don't keep partial/invalid token in memory/storage
                this.clearToken();
                resolve(false);
                return;
            }

            this.authToken = token;
            // Guardar directamente en localStorage de forma segura (única fuente de verdad)
            try { 
                localStorage.setItem('mole_jwt', token);
                localStorage.setItem('moleia_token', token);
                console.log("CRITICAL: Token persisted to localStorage");
            } catch (e) { 
                console.error('[ApiService] Error guardando token en localStorage'); 
            }
            // Return a resolved promise so callers can `await` this operation
            resolve(true);
        });
    }

    getToken() {
        // Si el token está guardado en memoria pero ya no existe en storage, lo consideramos inexistente.
        if (this.authToken) {
            const stored = localStorage.getItem('mole_jwt') || localStorage.getItem('moleia_token') || sessionStorage.getItem('mole_jwt');
            if (!stored) {
                // Token eliminado del storage (por ejemplo, usuario limpió cache). Descartamos el token en memoria.
                this.authToken = null;
                return null;
            }
            return this.authToken;
        }
        var saved = null;
        // Leer DIRECTAMENTE de localStorage (sin depender de window.getAuthToken)
        try { saved = localStorage.getItem('mole_jwt'); } catch (e) { saved = null; }
        if (!saved) {
            try { saved = localStorage.getItem('moleia_token'); } catch (e) { saved = null; }
        }
        if (!saved) {
            try { saved = sessionStorage.getItem('mole_jwt'); } catch (e) { saved = null; }
        }
        if (saved) {
            this.authToken = saved;
            return saved;
        }
        return null;
    }

    clearToken() {
        this.authToken = null;
        try { localStorage.removeItem('mole_jwt'); } catch (e) { /* ignore */ }
        try { sessionStorage.removeItem('mole_jwt'); } catch (e) { /* ignore */ }
        try { localStorage.removeItem('moleia_token'); } catch (e) { /* ignore */ }
    }

    _maskToken(token) {
        if (!token || typeof token !== 'string') return '';
        try {
            if (token.length <= 12) return token.replace(/.(?=.{4})/g, '*');
            return token.slice(0,6) + '…' + token.slice(-6);
        } catch (e) { return '***'; }
    }

    // Allow runtime override of the Authorization prefix (e.g. 'Token ', 'JWT ')
    setAuthPrefix(prefix) {
        if (typeof prefix !== 'string') return;
        this.authPrefix = prefix;
    }

    // Ensure token saved (Promise-friendly wrapper)
    ensureTokenSaved(token) {
        return this.setToken(token);
    }

    // ─── HEADER BUILDER ─────────────────────────────────────────────────

    buildHeaders(extra) {
        var headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
        var token = this.getToken();
        // Defensive: only attach Authorization when token is a non-empty string
        if (token && typeof token === 'string' && token.trim() !== '') {
            headers['Authorization'] = (this.authPrefix || 'Bearer ') + token;
        }
        // ---- CSRF handling ----
        try {
            // Look for the Django CSRF cookie (default name 'csrftoken')
            var csrfMatch = document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('csrftoken='));
            if (csrfMatch) {
                var csrfToken = csrfMatch.split('=')[1];
                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken;
                }
            }
        } catch (e) {
            // Silently ignore cookie parsing errors – request will fail and be reported downstream
        }
        if (extra) {
            for (var key in extra) {
                if (extra.hasOwnProperty(key)) {
                    headers[key] = extra[key];
                }
            }
        }
        return headers;
    }

    // ─── JWT HELPERS ─────────────────────────────────────────────────

    _decodeJwtPayload(token) {
        try {
            var parts = token.split('.');
            if (parts.length < 2) return null;
            var payload = parts[1];
            // atob can throw if invalid
            var json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
            return JSON.parse(json);
        } catch (e) {
            return null;
        }
    }

    isTokenExpired(token) {
        token = token || this.getToken();
        if (!token) return true;
        var payload = this._decodeJwtPayload(token);
        if (!payload || !payload.exp) return false; // cannot determine -> assume valid
        var now = Math.floor(Date.now() / 1000);
        var buffer = 10; // seconds buffer to mitigate clock skew (was 60)
        try {
            // If token was just written, consider it fresh and not expired for a short window
            if (this._freshToken && (Date.now() - this._freshToken) < 2000) {
                return false;
            }
        } catch (e) { /* ignore */ }
        return payload.exp <= now + buffer;
    }

    isTokenPresent() {
        return !!this.getToken();
    }

    // ─── TIMEOUT HELPER ─────────────────────────────────────────────────

    _getTimeout(endpoint) {
        var ep = endpoint.toLowerCase();
        for (var i = 0; i < this._aiEndpoints.length; i++) {
            if (ep.indexOf(this._aiEndpoints[i]) !== -1) {
                return this.aiTimeout;
            }
        }
        return this.defaultTimeout;
    }

    // ─── RESPONSE HANDLER ───────────────────────────────────────────────

    handleResponse(response) {
        var contentType = response.headers.get('content-type');
        var isJson = contentType && contentType.indexOf('application/json') !== -1;

        // Resolve payload as JSON when possible, otherwise as raw text
        var dataPromise = isJson ? response.json() : response.text();

        return dataPromise.then(function (data) {
            // COFEPRIS Disclaimer detection (only applies to JSON payloads)
            if (isJson && data && typeof data === 'object' && data.disclaimer) {
                window.dispatchEvent(new CustomEvent('disclaimerReceived', {
                    detail: { text: data.disclaimer }
                }));
            }

            if (!response.ok) {
                // Base message includes status code for transparency
                var errorMessage = 'Error ' + response.status;

                // Try to extract a meaningful message from the payload
                if (data) {
                    if (isJson && typeof data === 'object' && data !== null) {
                // Standard Django / DRF error shapes
                if (data.error) {
                    errorMessage = String(data.error);
                } else if (data.message) {
                    errorMessage = String(data.message);
                } else if (data.detail) {
                    // Handle Pydantic validation errors (array of detail objects)
                    if (Array.isArray(data.detail)) {
                        errorMessage = data.detail.map(err => `${err.loc.join('->')}: ${err.msg}`).join(' | ');
                    } else {
                        errorMessage = String(data.detail);
                    }
                } else {
                    // Validation errors: {field: ["msg"]}
                    var msgs = [];
                    for (var k in data) {
                        if (data.hasOwnProperty(k) && Array.isArray(data[k]) && data[k].length) {
                            msgs.push(String(data[k][0]));
                        }
                    }
                    if (msgs.length) {
                        errorMessage = msgs.join(' | ');
                    }
                }
            } else {
                // Non‑JSON response (plain‑text error). Use the raw text.
                errorMessage = data.trim();
            }
                }

                var error = new Error(errorMessage);
                error.status = response.status;
                error.data = data;
                throw error;
            }

            return data;
        });
    }

    // ─── FRIENDLY ERROR MESSAGES ────────────────────────────────────────

    _friendlyMessage(error) {
        if (error instanceof TypeError) {
            return 'Sin conexión al servidor. Verifica tu red.';
        }
        if (error.name === 'AbortError') {
            return 'La conexión es inestable. Reintentando...';
        }
        var s = error.status;
        if (s === 503) return 'El servicio de IA está procesando. Intenta en unos segundos.';
        if (s === 504) return 'Timeout del servidor. La conexión es inestable.';
        if (s === 429) return 'Demasiadas solicitudes. Espera un momento.';
        if (s === 401) return 'Sesión expirada. Vuelve a iniciar sesión.';
        if (s >= 500) return 'Error interno del servidor. Intenta más tarde.';
        return error.message || 'Error desconocido.';
    }

    // ─── REQUEST WITH RETRY + TIMEOUT ───────────────────────────────────

    _buildUrl(endpoint) {
        var rawUrl = this.baseUrl + endpoint;
        // Escudo Regex: Limpiar dobles barras excepto el protocolo (http://)
        return rawUrl.replace(/([^:]\/)\/+/g, "$1");
    }

    request(endpoint, method, body, customHeaders, options = {}) {
        var self = this;
// --- STEP 1: NORMALIZE ENDPOINT (Remove leading slash, query params, trailing slash) ---
var normalizedEndpoint = endpoint.trim();
// Remove leading '/' if present
if (normalizedEndpoint.charAt(0) === '/') {
    normalizedEndpoint = normalizedEndpoint.slice(1);
}
// Remove query parameters (everything after '?')
var queryPart = normalizedEndpoint.split('?')[1];
normalizedEndpoint = normalizedEndpoint.split('?')[0];
// Remove trailing '/' if present
if (normalizedEndpoint.charAt(normalizedEndpoint.length - 1) === '/') {
    normalizedEndpoint = normalizedEndpoint.slice(0, -1);
}
// Re-add query part if existed
if (queryPart) {
    normalizedEndpoint = normalizedEndpoint + '?' + queryPart;
}

// Ensure trailing slash before query string (prevents Django 301 redirect losing query params)
var urlParts = normalizedEndpoint.split('?');
if (urlParts[0].charAt(urlParts[0].length - 1) !== '/') {
    urlParts[0] = urlParts[0] + '/';
}
normalizedEndpoint = urlParts.join('?');

var url = self._buildUrl(normalizedEndpoint);
var timeout = self._getTimeout(normalizedEndpoint);
method = method || 'GET';
var silent = options.silent || false;

// --- STEP 2: WHITELIST CHECK (Bulletproof: matches normalizedEndpoint without trailing slash) ---
// Normalize even further: remove baseUrl prefix if somehow included
var fullUrl = self.baseUrl + normalizedEndpoint;
// Check if the normalizedEndpoint STARTS WITH 'auth' or 'plants/search' (no trailing slash required)
// Handles: auth, auth/login, plants/search, plants/search/?q=..., etc.
var publicRegex = /^(auth|plants\/search)/;
var isPublic = publicRegex.test(normalizedEndpoint);
// Fallback: also check fullUrl (in case baseUrl is included in normalizedEndpoint somehow)
if (!isPublic) {
    isPublic = /(auth|plants\/search)/.test(fullUrl);
}
if (isPublic) {
    options.allowAnonymous = true;
    console.log('[ApiService] Public endpoint detected:', normalizedEndpoint);
}

        // Enforce strict JWT presence and validity (Zero-Trust)
        var token = self.getToken();

        // HARD REJECT: immediate fail if endpoint requires auth and token is missing
        if (!options.allowAnonymous && (!token || typeof token !== 'string' || token.trim() === '')) {
            var errNoToken = new Error('Local_401_Unauthorized: Missing token');
            errNoToken.status = 401;
            if (!silent) {
                ApiService.showToast('Sesión no autenticada. Inicia sesión.', 'error');
            }
            return Promise.reject(errNoToken);
        }

        // Pre-flight: avoid sending tokens that expire in <10s (with fresh-token bypass)
        try {
            if (token && typeof token === 'string' && token.trim() !== '') {
                if (self.isTokenExpired(token)) {
                    // ISSUE-FE-06: If route is public, silently drop token and proceed anonymously
                    if (options.allowAnonymous) {
                        self.clearToken();
                        token = null;
                        console.log('[ApiService] Token expired on public route, proceeding anonymously.');
                    } else {
                        // Token about to expire — clear and redirect to login
                        self.clearToken();
                        ApiService.showToast('Sesión a punto de expirar. Vuelve a iniciar sesión.', 'error');
                        window.location.href = '/login/';
                        var err = new Error('TOKEN_EXPIRING');
                        err.status = 401;
                        return Promise.reject(err);
                    }
                }
            }
        } catch (e) {
            console.warn('[ApiService] Pre-flight token check failed, procediendo con limpieza.');
            self.clearToken();
            if (options.allowAnonymous) token = null;
        }

        // Defensive guard: if a token exists but is not a plain string, clear it and fail early
        if (token && typeof token !== 'string') {
            console.error('[ApiService] Invalid token format detected in client. Clearing token.');
            self.clearToken();
            var errInvalid = new Error('INVALID_TOKEN_FORMAT');
            errInvalid.status = 401;
            if (!silent) ApiService.showToast('Token inválido en cliente. Reautentifica.', 'error');
            return Promise.reject(errInvalid);
        }
        function attemptRequest(attempt) {
            return new Promise(function (resolve, reject) {
                var controller = new AbortController();
                var timer = setTimeout(function () { controller.abort(); }, timeout);
                
                // Si el usuario provee un signal externo, abortamos el interno cuando este dispare
                if (options.signal) {
                    options.signal.addEventListener('abort', () => controller.abort());
                }

                var headers = self.buildHeaders(customHeaders);
                var fetchOptions = {
                    method: method.toUpperCase(),
                    headers: headers,
                    signal: controller.signal
                };

                // Body handling
                if (body !== null && body !== undefined && method !== 'GET' && method !== 'HEAD') {
                    if (body instanceof FormData) {
                        // Let browser set Content-Type with boundary for multipart
                        delete fetchOptions.headers['Content-Type'];
                        fetchOptions.body = body;
                    } else {
                        fetchOptions.body = JSON.stringify(body);
                    }
                }

                // Telemetry: log token presence and headers sent for debugging (Supervisor)
                try {
                    if (token && typeof token === 'string' && token.trim() !== '') {
                        console.log(" SUCCESS ACCESS:", self._maskToken(token));
                    } else {
                        console.log(" ANONYMOUS ACCESS");
                    }
                } catch (e) { /* ignore logging errors */ }
                try {
                    console.log(" HEADERs HIGH:", headers);
                } catch (e) { /* ignore logging errors */ }

                fetch(url, fetchOptions)
                    .then(function (response) {
                        clearTimeout(timer);
                        return self.handleResponse(response);
                    })
                    .then(resolve)
                    .catch(function (error) {
                        clearTimeout(timer);

                        // Only retry on network/timeout errors
                        var isRetryable = (error instanceof TypeError) || (error.name === 'AbortError') || (error.status >= 500 && error.status < 600);

                        if (!isRetryable || attempt >= self.maxRetries) {
                            reject(error);
                            return;
                        }

                        // Exponential backoff: 1s, 2s, 4s
var delay = self.retryBaseDelay * Math.pow(2, attempt);
                       if (!silent) {
                           console.warn('[ApiService] Retry ' + (attempt + 1) + '/' + self.maxRetries + ' en ' + delay + 'ms...');
                           ApiService.showToast('Reintentando conexión (intento ' + (attempt + 1) + '/' + self.maxRetries + ')...', 'warn');
                       }
                        setTimeout(function () {
                            attemptRequest(attempt + 1).then(resolve).catch(reject);
                        }, delay);
                    });
            });
        }

        return attemptRequest(0).catch(function (error) {
            if (!silent) {
                var friendlyMsg = self._friendlyMessage(error);
                // Avoid redundant toasts when form already shows error (register/login)
                var isFormError = (normalizedEndpoint.includes('auth/register') || normalizedEndpoint.includes('auth/login'));
                if (!isFormError) {
                    ApiService.showToast(friendlyMsg, 'error');
                }
                console.error('[ApiService] ' + method + ' ' + endpoint + ' falló: Error ' + (error.status || '') + ': ' + error.message);
            }
            throw error;
        });
    }

    // ─── HELPER METHODS ─────────────────────────────────────────────────

    get(endpoint, options = {}) {
        return this.request(endpoint, 'GET', null, options.headers, options);
    }

    post(endpoint, body, options = {}) {
        return this.request(endpoint, 'POST', body, options.headers, options);
    }

    put(endpoint, body, options = {}) {
        return this.request(endpoint, 'PUT', body, options.headers, options);
    }

    upload(endpoint, formData, options = {}) {
        return this.request(endpoint, 'POST', formData, options.headers, options);
    }

    // ─── TOAST NOTIFICATIONS (Terminal Style) ───────────────────────────

    static showToast(message, type) {
        type = type || 'info';
        var container = document.getElementById('toast-container');

        // OWASP fix: never expose raw server errors via alert()
        // Silently log if toast container is absent (e.g. pages without #toast-container)
        if (!container) {
            console.warn('[Toast fallback] ' + type + ': ' + message);
            return;
        }

        var prefixes = {
            error: '[ ERROR ]',
            warn: '[ WARN  ]',
            info: '[ INFO  ]',
            success: '[ OK    ]'
        };
        var prefix = prefixes[type] || prefixes.info;

        var toast = document.createElement('div');
        toast.className = 'terminal-toast terminal-toast--' + type;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = '<span class="toast-prefix">' + prefix + '</span> ' + message;

        container.appendChild(toast);

        // Auto-remove after 6s
        setTimeout(function () {
            toast.classList.add('toast-fade-out');
            setTimeout(function () { toast.remove(); }, 400);
        }, 6000);
    }
}

// Global instance (use instance, not class, so methods like .post() work directly)
window.ApiService = new ApiService();
window.moleApi = window.ApiService;

// ============ CMD CENTER API METHODS ============

/**
 * Get KPI dashboard data
 * GET /api/v1/metrics/kpi/
 */
ApiService.getKPIData = function() {
    return this.get('metrics/kpi/');
};

/**
 * Get IoT fleet status
 * GET /api/v1/iot/fleet/
 */
ApiService.getIoTFleet = function() {
    return this.get('iot/fleet/');
};

/**
 * Get ML model metrics
 * GET /api/v1/ml/metrics/
 */
ApiService.getMLMetrics = function() {
    return this.get('ml/metrics/');
};

/**
 * Get alerts list
 * GET /api/v1/alerts/
 */
ApiService.getAlerts = function() {
    return this.get('alerts/');
};

/**
 * Acknowledge an alert
 * POST /api/v1/alerts/{id}/acknowledge/
 */
ApiService.acknowledgeAlert = function(alertId) {
    return this.post('alerts/' + alertId + '/acknowledge/');
};

/**
 * Delete an alert
 * DELETE /api/v1/alerts/{id}/
 */
ApiService.deleteAlert = function(alertId) {
    return this.delete('alerts/' + alertId + '/');
};

/**
 * Trigger model training
 * POST /api/v1/ml/train/
 */
ApiService.triggerTraining = function(data) {
    return this.post('ml/train/', data);
};

/**
 * Deploy model version
 * POST /api/v1/ml/deploy/
 */
ApiService.deployModel = function(data) {
    return this.post('ml/deploy/', data);
};

/**
 * Export dashboard data
 * GET /api/v1/reports/export/
 */
ApiService.exportData = function() {
    return this.get('reports/export/');
};