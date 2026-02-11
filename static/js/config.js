// Configuración Global del Sistema
window.APP_CONFIG = {
    // URL de tu Backend Django
    API_URL: 'http://127.0.0.1:8000/api/v1/',
    
    // Credenciales de Supabase (manteniendo configuración real)
    SUPABASE: {
        URL: 'https://osmhchhvdutkmimrclyq.supabase.co',
        ANON_KEY: 'sb_publishable_fz496ixqzal2rT2RK9zrRQ_DlFCIBNk'
    }
};

// Mantener compatibilidad con el código existente
window.SUPABASE_CONFIG = window.APP_CONFIG.SUPABASE;

console.log("Configuración de Mole-IA cargada.");