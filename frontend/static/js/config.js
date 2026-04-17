// ==========================================================
// CONFIGURACIÓN GLOBAL
// ==========================================================
window.AppConfig = {
    API_BASE_URL: window.location.origin + '/api/v1',
    POLLING_INTERVAL: 5000, // 5 segundos para sensores
    AI_TIMEOUT: 120000      // 2 minutos para IA
};

// Helpers Globales para JWT (Unificando mole_jwt y moleia_token)
window.getAuthToken = function() {
    return window.getAuthToken() || window.getAuthToken() || sessionStorage.getItem('mole_jwt');
};

window.setAuthToken = function(token) {
    localStorage.setItem('moleia_token', token);
    localStorage.setItem('mole_jwt', token);
};

window.clearAuthToken = function() {
    localStorage.removeItem('moleia_token');
    localStorage.removeItem('mole_jwt');
    sessionStorage.removeItem('mole_jwt');
};