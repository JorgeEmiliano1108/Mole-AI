import { spinner } from '../ui/spinner.js';
import { el, safeRender } from '../ui/dom.js';
import { apiService } from '../api/ApiService.js';

function renderDiagnosisRow(label, value, valueClass) {
    return el('p', { className: 'text-xs' },
        el('span', { className: 'text-mole-text-dim' }, label),
        el('span', { className: `font-bold ${valueClass}` }, value)
    );
}

function renderDiagnosisResult(data) {
    return el('div', { className: 'space-y-2' },
        renderDiagnosisRow('ESPECIE: ', data.species || 'DESCONOCIDA', 'text-mole-accent'),
        renderDiagnosisRow('CONDICIÓN: ', data.condition || 'NO DETECTADA', 'text-mole-cyan'),
        renderDiagnosisRow('SEVERIDAD: ', data.severity ? data.severity.toUpperCase() : 'N/A', 'text-mole-amber'),
        renderDiagnosisRow('PH ESTIMADO: ',
            data.ph_predicted != null ? String(data.ph_predicted) : 'N/A',
            'text-mole-green'
        ),
        renderDiagnosisRow('CONFIANZA: ',
            data.confidence ? (data.confidence * 100).toFixed(1) + '%' : 'N/A',
            'text-mole-text'
        )
    );
}

function renderDiagnosisError(error) {
    const msg = error.data?.detail?.title || error.message || "El servidor de IA está temporalmente fuera de línea. Por favor, reintente en unos minutos.";
    return el('div', { className: 'space-y-2' },
        renderDiagnosisRow('ESPECIE: ', 'SISTEMA DESCONECTADO', 'text-mole-red'),
        renderDiagnosisRow('CONDICIÓN: ', 'Motor de Visión Inaccesible', 'text-mole-red'),
        renderDiagnosisRow('ERROR: ', msg, 'text-mole-red')
    );
}

// ==========================================================
// 8. FLUJO DE DIAGN STICO 
// ==========================================================

/**
 * PROCESAMIENTO DE IMAGEN: Captura el archivo, lo muestra y lo env a al servidor.
 */
/**
 * PROCESAMIENTO DE IMAGEN: Captura el archivo, lo muestra y lo env a al RAG/CNN.
 */
async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 1. Pre-visualizaci n inmediata (Cero Base64)
    const preview = document.getElementById('main-img');
    const placeholder = document.getElementById('video-placeholder');
    if (preview) {
        // Liberar URL anterior si existe para evitar memory leaks
        if (preview.src && preview.src.startsWith('blob:')) {
            URL.revokeObjectURL(preview.src);
        }
        preview.src = URL.createObjectURL(file);
        preview.classList.remove('hidden');
    }
    if (placeholder) {
        placeholder.classList.add('hidden');
    }

    // 2. Activamos la pantalla de carga y deshabilitamos input
    const camInput = event.target;
    camInput.disabled = true;
    spinner.showGlobal();

    // 3. Preparaci n del Payload
    const formData = new FormData();
    formData.append('image', file); // Mismo nombre que espera tu DiagnosticRequestSerializer
    
    const currentOp = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
    formData.append('operator', currentOp);

    const term = document.getElementById('diagnostic-term');
    if (!term) {
        console.error("CRITICAL DOM ERROR: No se encontr\u00f3 '#diagnostic-term' en el documento.");
        return;
    }
    try {

        // Zero-Trust: Validamos token antes de disparar a la red
        if (!apiService.isTokenPresent()) {
            throw new Error("Acceso denegado: Se requiere autenticaci\u00f3n para usar el Motor IA.");
        }

        //   USO DE API SERVICE: Endpoint 'vision/analyze/' mapeado en Gateway
        // Debug: log Authorization header (masked) before request - helpful for 401 debugging
        console.log('Authorization header \u2192', apiService.buildHeaders().Authorization);
        const data = await apiService.upload('vision/analyze/', formData);

        if (term) {
            safeRender(term, renderDiagnosisResult(data));
        }

        if (data.severity && data.severity.toLowerCase() === 'high' && typeof window.logPlantIssue === 'function') {
            window.logPlantIssue(data.species || "ESPECIE ESCANEADA", data.condition);
        }

    } catch (error) {
        console.error("> [ ERROR CR\u00cdTICO ] Error en conexi\u00f3n con el motor de visi\u00f3n:", error);
        // If unauthorized, clear token and redirect to login
        if (error && error.status === 401) {
            apiService.clearToken();
            window.location.href = '/login.html';
            return; // Skip UI update, page navigation will occur
        }
        if (term) {
            safeRender(term, renderDiagnosisError(error));
        }
        
    } finally {
        // 5. Transici n final
        spinner.hideGlobal();
        camInput.disabled = false;
        
        const cameraInput = document.getElementById('camera-input');
        if (cameraInput) cameraInput.value = '';
    }
}

/**
 * CIERRE DE INTERFAZ DE DIAGN STICO
 */

/**
 * LISTENER INICIALIZADOR
 */
document.addEventListener('DOMContentLoaded', () => {
    const camInput = document.getElementById('camera-input');
    if (camInput) {
        camInput.addEventListener('change', handleImageUpload);
    }
});