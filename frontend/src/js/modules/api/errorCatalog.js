/**
 * errorCatalog.js — Mole.AI Central Error Catalog
 * ═══════════════════════════════════════════════════
 * Mapeo centralizado de códigos HTTP → configuración de error.
 * Todos los módulos deben consultar este catálogo en lugar de
 * hardcodear mensajes o redirecciones.
 *
 * Cada entrada tiene:
 *   - title:    Título corto para la UI (estilo terminal)
 *   - message:  Mensaje amigable para el usuario
 *   - action:   CTA principal recomendado
 *   - severity: 'critical' | 'high' | 'medium' | 'low'
 *   - redirect: URL de redirección (null = manejar inline)
 *   - isPage:   true si tiene HTML separado dedicado
 */

const ERROR_CATALOG = {
    // ── Client Errors ──────────────────────────────────────────────
    400: {
        title: 'SOLICITUD INVÁLIDA',
        message: 'Los datos enviados no son válidos. Revisa los campos del formulario.',
        action: 'Corregir campos',
        severity: 'medium',
        redirect: null,
        isPage: false
    },
    401: {
        title: 'SESIÓN EXPIRADA',
        message: 'Tu sesión ha caducado o no estás autenticado. Inicia sesión de nuevo.',
        action: 'Iniciar sesión',
        severity: 'high',
        redirect: '/login.html',
        isPage: false
    },
    403: {
        title: 'ACCESO DENEGADO',
        message: 'No tienes los privilegios necesarios para acceder a este recurso.',
        action: 'Re-autenticar',
        severity: 'critical',
        redirect: '/403.html',
        isPage: true
    },
    404: {
        title: 'RECURSO NO ENCONTRADO',
        message: 'El recurso solicitado no existe o fue movido.',
        action: 'Volver al inicio',
        severity: 'medium',
        redirect: '/404.html',
        isPage: true
    },
    409: {
        title: 'CONFLICTO DE DATOS',
        message: 'El recurso que intentas crear ya existe en el sistema.',
        action: 'Verificar datos',
        severity: 'medium',
        redirect: null,
        isPage: false
    },
    422: {
        title: 'DATOS NO PROCESABLES',
        message: 'El servidor no pudo procesar los datos enviados. Verifica el formato.',
        action: 'Revisar formulario',
        severity: 'medium',
        redirect: null,
        isPage: false
    },
    429: {
        title: 'LÍMITE DE SOLICITUDES',
        message: 'Has enviado demasiadas solicitudes. Espera unos momentos antes de reintentar.',
        action: 'Esperar',
        severity: 'medium',
        redirect: null,
        isPage: false
    },

    // ── Server Errors ──────────────────────────────────────────────
    500: {
        title: 'ERROR INTERNO',
        message: 'Ocurrió un error interno en el servidor. El equipo ha sido notificado.',
        action: 'Reintentar',
        severity: 'critical',
        redirect: '/500.html',
        isPage: true
    },
    501: {
        title: 'NO IMPLEMENTADO',
        message: 'Esta funcionalidad aún no está disponible. Estará lista próximamente.',
        action: 'Volver',
        severity: 'low',
        redirect: null,
        isPage: false
    },
    502: {
        title: 'PUERTA DE ENLACE',
        message: 'El servidor intermediario no pudo conectarse con el servicio. Reintenta en unos segundos.',
        action: 'Reintentar',
        severity: 'critical',
        redirect: '/500.html',
        isPage: true
    },
    503: {
        title: 'SERVICIO EN MANTENIMIENTO',
        message: 'El sistema está en mantenimiento programado. Intenta de nuevo en unos minutos.',
        action: 'Intentar más tarde',
        severity: 'high',
        redirect: '/503.html',
        isPage: true
    },
    504: {
        title: 'TIMEOUT DEL SERVIDOR',
        message: 'La conexión con el servidor tardó demasiado. La red puede estar inestable.',
        action: 'Reintentar',
        severity: 'high',
        redirect: '/500.html',
        isPage: true
    },

    // ── Special Cases ──────────────────────────────────────────────
    NETWORK_ERROR: {
        title: 'SIN CONEXIÓN',
        message: 'No se pudo conectar con el servidor. Verifica tu conexión a internet.',
        action: 'Verificar red',
        severity: 'critical',
        redirect: null,  // Fase 5 lo cambiará a '/offline.html' o banner
        isPage: false
    },
    TIMEOUT: {
        title: 'CONEXIÓN INESTABLE',
        message: 'La solicitud fue cancelada por timeout. Reintentando...',
        action: 'Esperar reintento',
        severity: 'high',
        redirect: null,
        isPage: false
    },
    RUNTIME_ERROR: {
        title: 'ERROR INESPERADO',
        message: 'Ocurrió un error inesperado en la aplicación. Recarga la página.',
        action: 'Recargar',
        severity: 'critical',
        redirect: null,
        isPage: false
    }
};

/**
 * Obtiene la configuración de error para un código HTTP o tipo especial.
 * @param {number|string} code — Código HTTP (400, 401, etc.) o tipo especial ('NETWORK_ERROR', etc.)
 * @returns {object} — Configuración del error, o un fallback genérico
 */
export function getErrorConfig(code) {
    if (ERROR_CATALOG[code]) {
        return { ...ERROR_CATALOG[code], code: code };
    }
    // Fallback para códigos no catalogados
    if (typeof code === 'number') {
        if (code >= 500) {
            return { ...ERROR_CATALOG[500], code: code, title: 'ERROR DE SERVIDOR ' + code };
        }
        if (code >= 400) {
            return { ...ERROR_CATALOG[400], code: code, title: 'ERROR DE CLIENTE ' + code };
        }
    }
    return {
        code: code,
        title: 'ERROR DESCONOCIDO',
        message: 'Ocurrió un error no identificado. Contacta al administrador.',
        action: 'Reintentar',
        severity: 'medium',
        redirect: null,
        isPage: false
    };
}

/**
 * Determina el tipo de error especial a partir de un objeto Error.
 * @param {Error} error — El error capturado
 * @returns {string|number} — Código HTTP o tipo especial ('NETWORK_ERROR', 'TIMEOUT')
 */
export function classifyError(error) {
    if (error instanceof TypeError) return 'NETWORK_ERROR';
    if (error.name === 'AbortError') return 'TIMEOUT';
    if (error.status) return error.status;
    return 'RUNTIME_ERROR';
}

/**
 * Obtiene el mensaje amigable para un error dado.
 * Reemplaza completamente a `_friendlyMessage()` en futuras fases.
 * @param {Error} error — El error capturado
 * @returns {string} — Mensaje amigable en español
 */
export function getFriendlyMessage(error) {
    var code = classifyError(error);
    var config = getErrorConfig(code);
    return config.message;
}

/**
 * Obtiene la URL de redirección para un error, si aplica.
 * @param {number|string} code — Código HTTP o tipo especial
 * @returns {string|null} — URL de redirección o null
 */
export function getErrorRedirect(code) {
    var config = getErrorConfig(code);
    return config.redirect;
}

// Export del catálogo completo para inspección/debug
export { ERROR_CATALOG };

// Exposición global para scripts no-module
window.ErrorCatalog = {
    getErrorConfig,
    classifyError,
    getFriendlyMessage,
    getErrorRedirect,
    ERROR_CATALOG
};
