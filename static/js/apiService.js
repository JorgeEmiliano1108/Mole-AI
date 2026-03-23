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
        this.baseUrl = 'http://localhost:8000/api/v1/';
        this.defaultTimeout = 30000;   // 30s for standard requests
        this.aiTimeout = 120000;       // 120s for AI/LLM endpoints
        this.maxRetries = 3;
        this.retryBaseDelay = 1000;    // 1s base, exponential backoff
        this._aiEndpoints = ['chat', 'diagnostic', 'llm', 'vision', 'rag', 'cnn'];

        // Session token (set after login)
        this.authToken = null;
        // Authorization prefix (use Bearer to match backend SupabaseAuthentication)
        this.authPrefix = 'Bearer ';
    }

    // ─── AUTH TOKEN MANAGEMENT ──────────────────────────────────────────

    setToken(token) {
        return new Promise(resolve => {
            // Defensive: only accept non-empty string tokens
            if (typeof token !== 'string' || token.trim() === '') {
                console.warn('ApiService.setToken: invalid token received, refusing to persist.', token);
                // Ensure we don't keep partial/invalid token in memory/storage
                this.clearToken();
                resolve(false);
                return;
            }

            this.authToken = token;
            sessionStorage.setItem('mole_jwt', token);
            console.log("CRITICAL: Token guardado físicamente");
            // Mecanismo de verificación síncrono
            if (sessionStorage.getItem('mole_jwt') !== token) {
                console.error("CRITICAL: Token no se ha guardado correctamente en sessionStorage");
            }
            // Return a resolved promise so callers can `await` this operation
            resolve(true);
        });
    }

    getToken() {
        if (this.authToken) return this.authToken;
        var saved = sessionStorage.getItem('mole_jwt');
        if (saved) {
            this.authToken = saved;
            return saved;
        }
        return null;
    }

    clearToken() {
        this.authToken = null;
        sessionStorage.removeItem('mole_jwt');
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
        if (token) {
            headers['Authorization'] = (this.authPrefix || 'Bearer ') + token;
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
        return payload.exp <= now;
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

        var dataPromise = isJson ? response.json() : response.text();

        return dataPromise.then(function (data) {
            // COFEPRIS Disclaimer detection
            if (isJson && data && typeof data === 'object' && data.disclaimer) {
                window.dispatchEvent(new CustomEvent('disclaimerReceived', {
                    detail: { text: data.disclaimer }
                }));
            }

            if (!response.ok) {
                var errorMessage = (data && data.message) ? data.message : 'Error HTTP ' + response.status;
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

    request(endpoint, method, body, customHeaders, options = {}) {
        var self = this;
        var cleanEndpoint = endpoint.charAt(0) === '/' ? endpoint.slice(1) : endpoint;
        var url = self.baseUrl + cleanEndpoint;
        var timeout = self._getTimeout(cleanEndpoint);
        method = method || 'GET';
        var silent = options.silent || false;

        // Enforce strict JWT presence and validity (Zero-Trust)
        var token = self.getToken();
        if (!options.allowAnonymous) {
            if (!token) {
                var errNoToken = new Error('NO_TOKEN');
                errNoToken.status = 401;
                if (!silent) {
                    ApiService.showToast('Sesión no autenticada. Inicia sesión.', 'error');
                }
                return Promise.reject(errNoToken);
            }

            if (self.isTokenExpired(token)) {
                var errExpired = new Error('EXPIRED_TOKEN');
                errExpired.status = 401;
                if (!silent) {
                    ApiService.showToast('Token vencido. Inicia sesión de nuevo.', 'error');
                }
                return Promise.reject(errExpired);
            }
        } else if (token && self.isTokenExpired(token)) {
            // Drop expired token so it doesn't pollute the anonymous request
            self.clearToken();
            token = null;
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

                var headers = self.buildHeaders(customHeaders);
                var options = {
                    method: method.toUpperCase(),
                    headers: headers,
                    signal: controller.signal
                };

                // Body handling
                if (body !== null && body !== undefined && method !== 'GET' && method !== 'HEAD') {
                    if (body instanceof FormData) {
                        // Let browser set Content-Type with boundary for multipart
                        delete options.headers['Content-Type'];
                        options.body = body;
                    } else {
                        options.body = JSON.stringify(body);
                    }
                }

                // Telemetry: log exact token and headers sent for debugging (Supervisor)
                try {
                    console.log("🔥 TOKEN EXACTO ENVIADO:", token);
                } catch (e) { /* ignore logging errors */ }
                try {
                    console.log("🔥 HEADERS COMPLETOS:", headers);
                } catch (e) { /* ignore logging errors */ }

                fetch(url, options)
                    .then(function (response) {
                        clearTimeout(timer);
                        return self.handleResponse(response);
                    })
                    .then(resolve)
                    .catch(function (error) {
                        clearTimeout(timer);

                        // Only retry on network/timeout errors
                        var isRetryable = (error instanceof TypeError) || (error.name === 'AbortError');

                        if (!isRetryable || attempt >= self.maxRetries) {
                            reject(error);
                            return;
                        }

                        // Exponential backoff: 1s, 2s, 4s
                        var delay = self.retryBaseDelay * Math.pow(2, attempt);
                        console.warn('[ApiService] Retry ' + (attempt + 1) + '/' + self.maxRetries + ' en ' + delay + 'ms...');
                        setTimeout(function () {
                            attemptRequest(attempt + 1).then(resolve).catch(reject);
                        }, delay);
                    });
            });
        }

        return attemptRequest(0).catch(function (error) {
            if (!silent) {
                var friendlyMsg = self._friendlyMessage(error);
                ApiService.showToast(friendlyMsg, 'error');
                console.error('[ApiService] ' + method + ' ' + endpoint + ' falló:', error);
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

        // Fallback to alert if toast container doesn't exist
        if (!container) {
            alert('[' + type.toUpperCase() + '] ' + message);
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

// Global instance
window.ApiService = ApiService;
window.moleApi = new ApiService();