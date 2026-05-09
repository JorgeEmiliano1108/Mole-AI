// ==========================================================
// CONFIGURACIÓN GLOBAL
// ==========================================================
window.AppConfig = {
    API_BASE_URL: window.location.origin + '/api/v1/',
    POLLING_INTERVAL: 5000, // 5 segundos para sensores
    AI_TIMEOUT: 120000      // 2 minutos para IA
};

// Helpers Globales para JWT (Unificando mole_jwt y moleia_token)
export function getAuthToken() {
    return localStorage.getItem('moleia_token') || localStorage.getItem('mole_jwt');
};

export function setAuthToken(token) {
    localStorage.setItem('moleia_token', token);
    localStorage.setItem('mole_jwt', token);
};

export function clearAuthToken() {
    localStorage.removeItem('moleia_token');
    localStorage.removeItem('mole_jwt');
};