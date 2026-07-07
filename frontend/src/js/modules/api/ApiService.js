import { showTacticalToast } from '../ui/tactical.js';

class ApiService {

    constructor() {
        this.baseUrl = window.AppConfig ? window.AppConfig.API_BASE_URL : window.location.origin + '/api/v1/';
        this.defaultTimeout = 30000;
        this.aiTimeout = 120000;
        this.maxRetries = 3;
        this.retryBaseDelay = 1000;
        this._aiEndpoints = ['chat', 'diagnostic', 'llm', 'vision', 'rag', 'cnn'];
        this.authToken = null;
        this.authPrefix = 'Bearer ';
        this.showToast = ApiService.showToast.bind(ApiService);
    }

    setToken(token) {
        return new Promise(resolve => {
            if (typeof token !== 'string' || token.trim() === '') {
                console.warn('ApiService.setToken: invalid token received, refusing to persist.');
                this.clearToken();
                resolve(false);
                return;
            }
            this.authToken = token;
            try {
                localStorage.setItem('mole_jwt', token);
                localStorage.setItem('moleia_token', token);
                console.log("CRITICAL: Token persisted to localStorage");
            } catch (e) {
                console.error('[ApiService] Error guardando token en localStorage');
            }
            resolve(true);
        });
    }

    getToken() {
        if (this.authToken) {
            const stored = localStorage.getItem('mole_jwt') || localStorage.getItem('moleia_token') || sessionStorage.getItem('mole_jwt');
            if (!stored) {
                this.authToken = null;
                return null;
            }
            return this.authToken;
        }
        var saved = null;
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
        try { localStorage.removeItem('mole_jwt'); } catch (e) { }
        try { sessionStorage.removeItem('mole_jwt'); } catch (e) { }
        try { localStorage.removeItem('moleia_token'); } catch (e) { }
    }

    _maskToken(token) {
        if (!token || typeof token !== 'string') return '';
        try {
            if (token.length <= 12) return token.replace(/.(?=.{4})/g, '*');
            return token.slice(0, 6) + '…' + token.slice(-6);
        } catch (e) { return '***'; }
    }

    setAuthPrefix(prefix) {
        if (typeof prefix !== 'string') return;
        this.authPrefix = prefix;
    }

    ensureTokenSaved(token) {
        return this.setToken(token);
    }

    buildHeaders(extra) {
        var headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
        var token = this.getToken();
        if (token && typeof token === 'string' && token.trim() !== '') {
            headers['Authorization'] = (this.authPrefix || 'Bearer ') + token;
        }
        try {
            var csrfMatch = document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('csrftoken='));
            if (csrfMatch) {
                var csrfToken = csrfMatch.split('=')[1];
                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken;
                }
            }
        } catch (e) {
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

    _decodeJwtPayload(token) {
        try {
            var parts = token.split('.');
            if (parts.length < 2) return null;
            var payload = parts[1];
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
        if (!payload || !payload.exp) return false;
        var now = Math.floor(Date.now() / 1000);
        var buffer = 10;
        try {
            if (this._freshToken && (Date.now() - this._freshToken) < 2000) {
                return false;
            }
        } catch (e) { }
        return payload.exp <= now + buffer;
    }

    isTokenPresent() {
        return !!this.getToken();
    }

    _getTimeout(endpoint) {
        var ep = endpoint.toLowerCase();
        for (var i = 0; i < this._aiEndpoints.length; i++) {
            if (ep.indexOf(this._aiEndpoints[i]) !== -1) {
                return this.aiTimeout;
            }
        }
        return this.defaultTimeout;
    }

    handleResponse(response) {
        var contentType = response.headers.get('content-type');
        var isJson = contentType && contentType.indexOf('application/json') !== -1;
        var dataPromise = isJson ? response.json() : response.text();

        return dataPromise.then(function (data) {
            if (isJson && data && typeof data === 'object' && data.disclaimer) {
                window.dispatchEvent(new CustomEvent('disclaimerReceived', {
                    detail: { text: data.disclaimer }
                }));
            }

            if (!response.ok) {
                var errorMessage = 'Error ' + response.status;

                if (data) {
                    if (isJson && typeof data === 'object' && data !== null) {
                        if (data.error) {
                            errorMessage = String(data.error);
                        } else if (data.message) {
                            errorMessage = String(data.message);
                        } else if (data.detail) {
                            if (Array.isArray(data.detail)) {
                                errorMessage = data.detail.map(err => `${err.loc.join('->')}: ${err.msg}`).join(' | ');
                            } else {
                                errorMessage = String(data.detail);
                            }
                        } else {
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

    _buildUrl(endpoint) {
        const base = this.baseUrl.replace(/\/+$/g, '');
        const cleanPath = endpoint.replace(/^\/+/, '');
        return `${base}/${cleanPath}`;
    }

    request(endpoint, method, body, customHeaders, options = {}) {
        var self = this;
        var normalizedEndpoint = endpoint.trim();
        if (normalizedEndpoint.charAt(0) === '/') {
            normalizedEndpoint = normalizedEndpoint.slice(1);
        }
        var queryPart = normalizedEndpoint.split('?')[1];
        normalizedEndpoint = normalizedEndpoint.split('?')[0];
        if (normalizedEndpoint.charAt(normalizedEndpoint.length - 1) === '/') {
            normalizedEndpoint = normalizedEndpoint.slice(0, -1);
        }
        if (queryPart) {
            normalizedEndpoint = normalizedEndpoint + '?' + queryPart;
        }

        var urlParts = normalizedEndpoint.split('?');
        if (urlParts[0].charAt(urlParts[0].length - 1) !== '/') {
            urlParts[0] = urlParts[0] + '/';
        }
        normalizedEndpoint = urlParts.join('?');

        var url = self._buildUrl(normalizedEndpoint);
        var timeout = self._getTimeout(normalizedEndpoint);
        method = method || 'GET';
        var silent = options.silent || false;

        var fullUrl = self.baseUrl + normalizedEndpoint;
        var publicRegex = /^(auth|plants\/search)/;
        var isPublic = publicRegex.test(normalizedEndpoint);
        if (!isPublic) {
            isPublic = /(auth|plants\/search)/.test(fullUrl);
        }
        if (isPublic) {
            options.allowAnonymous = true;
            console.log('[ApiService] Public endpoint detected:', normalizedEndpoint);
        }

        var token = self.getToken();

        if (!options.allowAnonymous && (!token || typeof token !== 'string' || token.trim() === '')) {
            var errNoToken = new Error('Local_401_Unauthorized: Missing token');
            errNoToken.status = 401;
            if (!silent) {
                ApiService.showToast('Sesión no autenticada. Inicia sesión.', 'error');
            }
            return Promise.reject(errNoToken);
        }

        try {
            if (token && typeof token === 'string' && token.trim() !== '') {
                if (self.isTokenExpired(token)) {
                    if (options.allowAnonymous) {
                        self.clearToken();
                        token = null;
                        console.log('[ApiService] Token expired on public route, proceeding anonymously.');
                    } else {
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

                if (options.signal) {
                    options.signal.addEventListener('abort', () => controller.abort());
                }

                var headers = self.buildHeaders(customHeaders);
                var fetchOptions = {
                    method: method.toUpperCase(),
                    headers: headers,
                    signal: controller.signal
                };

                if (body !== null && body !== undefined && method !== 'GET' && method !== 'HEAD') {
                    if (body instanceof FormData) {
                        delete fetchOptions.headers['Content-Type'];
                        fetchOptions.body = body;
                    } else {
                        fetchOptions.body = JSON.stringify(body);
                    }
                }

                try {
                    if (token && typeof token === 'string' && token.trim() !== '') {
                        console.log(" SUCCESS ACCESS:", self._maskToken(token));
                    } else {
                        console.log(" ANONYMOUS ACCESS");
                    }
                } catch (e) { }
                try {
                    console.log(" HEADERs HIGH:", headers);
                } catch (e) { }

                fetch(url, fetchOptions)
                    .then(function (response) {
                        clearTimeout(timer);
                        return self.handleResponse(response);
                    })
                    .then(resolve)
                    .catch(function (error) {
                        clearTimeout(timer);

                        var isRetryable = (error instanceof TypeError) || (error.name === 'AbortError') || (error.status >= 500 && error.status < 600);

                        if (!isRetryable || attempt >= self.maxRetries) {
                            reject(error);
                            return;
                        }

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
                var isFormError = (normalizedEndpoint.includes('auth/register') || normalizedEndpoint.includes('auth/login'));
                if (!isFormError) {
                    ApiService.showToast(friendlyMsg, 'error');
                }
                console.error('[ApiService] ' + method + ' ' + endpoint + ' falló: Error ' + (error.status || '') + ': ' + error.message);
            }
            throw error;
        });
    }

    get(endpoint, options = {}) {
        return this.request(endpoint, 'GET', null, options.headers, options);
    }

    post(endpoint, body, options = {}) {
        return this.request(endpoint, 'POST', body, options.headers, options);
    }

    put(endpoint, body, options = {}) {
        return this.request(endpoint, 'PUT', body, options.headers, options);
    }

    delete(endpoint, options = {}) {
        return this.request(endpoint, 'DELETE', null, options);
    }

    upload(endpoint, formData, options = {}) {
        return this.request(endpoint, 'POST', formData, options.headers, options);
    }

    static showToast(message, type) {
        const typeMap = { error: 'error', warn: 'warn', info: 'info', success: 'success' };
        showTacticalToast(message, typeMap[type] || 'info');
    }

    getKPIData() {
        return this.get('metrics/kpi/');
    }

    getIoTFleet() {
        return this.get('iot/fleet/');
    }

    getMLMetrics() {
        return this.get('ml/metrics/');
    }

    getAlerts() {
        return this.get('alerts/');
    }

    acknowledgeAlert(alertId) {
        return this.post('alerts/' + alertId + '/acknowledge/');
    }

    deleteAlert(alertId) {
        return this.delete('alerts/' + alertId + '/');
    }

    triggerTraining(data) {
        return this.post('ml/train/', data);
    }

    deployModel(data) {
        return this.post('ml/deploy/', data);
    }

    exportData() {
        return this.get('reports/export/');
    }
}

export const apiService = new ApiService();
