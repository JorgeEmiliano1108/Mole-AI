import { moleApi } from '../api/apiService.js';
import { spinner } from '../ui/spinner.js';
// ==========================================================
// 8. FLUJO DE DIAGNÓSTICO 
// ==========================================================

/**
 * PROCESAMIENTO DE IMAGEN: Captura el archivo, lo muestra y lo envía al servidor.
 */
/**
 * PROCESAMIENTO DE IMAGEN: Captura el archivo, lo muestra y lo envía al RAG/CNN.
 */
async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 1. Pre-visualización inmediata (Cero Base64)
    const preview = document.getElementById('scanned-image-preview');
    if (preview) {
        // Liberar URL anterior si existe para evitar memory leaks
        if (preview.src && preview.src.startsWith('blob:')) {
            URL.revokeObjectURL(preview.src);
        }
        preview.src = URL.createObjectURL(file);
    }

    // 2. Activamos la pantalla de carga y deshabilitamos input
    const camInput = event.target;
    camInput.disabled = true;
    spinner.showGlobal();

    // 3. Preparación del Payload
    const formData = new FormData();
    formData.append('image', file); // Mismo nombre que espera tu DiagnosticRequestSerializer
    
    const currentOp = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
    formData.append('operator', currentOp);

    try {
        // Zero-Trust: Validamos token antes de disparar a la red
        if (!moleApi.isTokenPresent()) {
            throw new Error("Acceso denegado: Se requiere autenticación para usar el Motor IA.");
        }

        // 🚀 USO DE API SERVICE: Endpoint 'diagnostic/' mapeado en tu backend
        const data = await moleApi.upload('diagnostic/', formData);

        // 4. Mapeo defensivo: El backend retorna 'analysis' (string largo), 
        // pero la UI busca datos particionados. Asignamos valores por defecto si no vienen particionados.
        document.getElementById('diag-species').innerText = data.species || "ESPECIE ESCANEADA";
        document.getElementById('diag-status').innerText = data.status || "ANÁLISIS COMPLETADO";
        document.getElementById('diag-ph').innerText = data.ph || "N/A";
        document.getElementById('diag-treatment').innerText = data.treatment || data.analysis || "Procesamiento finalizado sin observaciones adicionales.";

        if (data.status && data.status.toLowerCase().includes('crítico') && typeof logPlantIssue === 'function') {
            logPlantIssue(data.species || "ESPECIE ESCANEADA", data.treatment || data.analysis);
        }

    } catch (error) {
        console.error("> [ ERROR CRÍTICO ] Error en conexión con el motor de visión:", error);
        document.getElementById('diag-species').innerText = "ERROR DE CONEXIÓN";
        document.getElementById('diag-status').innerText = "Fallo al contactar MS1 (Visión).";
        document.getElementById('diag-ph').innerText = "ERR";
        document.getElementById('diag-treatment').innerText = error.message || "Verifique la red del clúster central y el estado del contenedor ms1_vision.";
        
    } finally {
        // 5. Transición final
        spinner.hideGlobal();
        camInput.disabled = false;
        
        const resultModal = document.getElementById('diagnosis-result-modal');
        if (resultModal) resultModal.classList.remove('hidden');
        
        const cameraInput = document.getElementById('camera-input');
        if (cameraInput) cameraInput.value = '';
    }
}

/**
 * CIERRE DE INTERFAZ DE DIAGNÓSTICO
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