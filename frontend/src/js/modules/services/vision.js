import { spinner } from '../ui/spinner.js';
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
        if (!window.ApiService.isTokenPresent()) {
            throw new Error("Acceso denegado: Se requiere autenticaci\u00f3n para usar el Motor IA.");
        }

        //   USO DE API SERVICE: Endpoint 'vision/analyze/' mapeado en Gateway
        // Debug: log Authorization header (masked) before request - helpful for 401 debugging
        console.log('Authorization header \u2192', window.ApiService.buildHeaders().Authorization);
        const data = await window.ApiService.upload('vision/analyze/', formData);

        if (term) {
            term.innerHTML = `
                <div class="space-y-2">
                    <p class="text-xs"><span class="text-mole-text-dim">ESPECIE:</span> <span class="text-mole-accent font-bold">${data.species || 'DESCONOCIDA'}</span></p>
                    <p class="text-xs"><span class="text-mole-text-dim">CONDICI\u00d3N:</span> <span class="text-mole-cyan font-bold">${data.condition || 'NO DETECTADA'}</span></p>
                    <p class="text-xs"><span class="text-mole-text-dim">SEVERIDAD:</span> <span class="text-mole-amber font-bold">${data.severity ? data.severity.toUpperCase() : 'N/A'}</span></p>
                    <p class="text-xs"><span class="text-mole-text-dim">PH ESTIMADO:</span> <span class="text-mole-green font-bold">${data.ph_predicted !== null && data.ph_predicted !== undefined ? data.ph_predicted : 'N/A'}</span></p>
                    <p class="text-xs"><span class="text-mole-text-dim">CONFIANZA:</span> <span class="text-mole-text font-bold">${data.confidence ? (data.confidence * 100).toFixed(1) + '%' : 'N/A'}</span></p>
                </div>
            `;
        }

        if (data.severity && data.severity.toLowerCase() === 'high' && typeof logPlantIssue === 'function') {
            logPlantIssue(data.species || "ESPECIE ESCANEADA", data.condition);
        }

    } catch (error) {
        console.error("> [ ERROR CR\u00cdTICO ] Error en conexi\u00f3n con el motor de visi\u00f3n:", error);
        // If unauthorized, clear token and redirect to login
        if (error && error.status === 401) {
            window.ApiService.clearToken();
            window.location.href = '/login.html';
            return; // Skip UI update, page navigation will occur
        }
        if (term) {
                term.innerHTML = `
                <div class="space-y-2">
                    <p class="text-xs"><span class="text-mole-text-dim">ESPECIE:</span> <span class="text-mole-red font-bold">SISTEMA DESCONECTADO</span></p>
                    <p class="text-xs"><span class="text-mole-text-dim">CONDICI\u00d3N:</span> <span class="text-mole-red font-bold">Motor de Visi\u00f3n Inaccesible</span></p>
                    <p class="text-xs"><span class="text-mole-text-dim">ERROR:</span> <span class="text-mole-red">${
                        // Prefer detailed server message if available
                        error.data?.detail?.title || error.message || "El servidor de IA est\u00e1 temporalmente fuera de l\u00ednea. Por favor, reintente en unos minutos."
                    }</span></p>
                </div>
            `;
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