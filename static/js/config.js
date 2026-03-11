// Configuración Global del Sistema (URLs dinámicas para Local / Producción)
(() => {
    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';

    // Base API expuesta al frontend (include trailing slash)
    const API_URL = (window.APP_CONFIG && window.APP_CONFIG.API_URL) || (isLocal ? 'http://127.0.0.1:8000/api/v1/' : '/api/v1/');

    // URL del servicio IA (FastAPI) - en producción debe ser relativo o proxied
    const AI_API_URL = (window.APP_CONFIG && window.APP_CONFIG.AI_API_URL) || (isLocal ? 'http://127.0.0.1:8001/api/v1/' : '/api/v1/');

    window.APP_CONFIG = {
        API_URL: API_URL,
        AI_API_URL: AI_API_URL,
        SUPABASE: {
            URL: 'https://osmhchhvdutkmimrclyq.supabase.co',
            ANON_KEY: 'sb_publishable_fz496ixqzal2rT2RK9zrRQ_DlFCIBNk'
        }
    };
})();

// Mantener compatibilidad con el código existente
window.SUPABASE_CONFIG = window.APP_CONFIG.SUPABASE;

console.log("Configuración de Mole-IA cargada.");