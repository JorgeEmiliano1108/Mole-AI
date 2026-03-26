// ==========================================================
// 8. FLUJO DE DIAGNÓSTICO (CÁMARA Y MOTOR DE IA) [BACKEND ESTRICTO]
// ==========================================================

/**
 * PROCESAMIENTO DE IMAGEN: Captura el archivo, lo muestra y lo envía al servidor.
 */
async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 1. Pre-visualización inmediata (Feedback visual en la UI)
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('scanned-image-preview');
        if (preview) preview.src = e.target.result;
    };
    reader.readAsDataURL(file);

    // 2. Activamos la pantalla de carga (Efecto de escaneo)
    const loadingModal = document.getElementById('loading-scan-modal');
    if (loadingModal) loadingModal.classList.remove('hidden');

    // 3. Preparación de datos (Multipart/FormData para imágenes)
    const formData = new FormData();
    formData.append('image', file);
    
    // Extraemos el ID del operador actual para el reporte
    const currentOp = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
    formData.append('operator_id', currentOp);

    try {
        const token = localStorage.getItem('moleia_token');
        
        if (!token) throw new Error("Acceso denegado: Se requiere autenticación para usar el Motor IA.");

        /* ========================================================
           🚀 CONEXIÓN CON BACKEND (MOTOR DE VISIÓN IA)
           ======================================================== */
        const response = await fetch('http://localhost:3000/api/v1/diagnose/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
                // OJO: NUNCA poner 'Content-Type': 'multipart/form-data' manual aquí, 
                // el navegador debe calcular el "boundary" automáticamente.
            },
            body: formData 
        });

        if (!response.ok) throw new Error(`Fallo en servidor botánico. Código: ${response.status}`);

        const data = await response.json();

        // 4. Llenar la tarjeta de diagnóstico con los datos REALES del backend
        document.getElementById('diag-species').innerText = data.species || "ESPECIE DESCONOCIDA";
        document.getElementById('diag-status').innerText = data.status || "ESTADO INDETERMINADO";
        document.getElementById('diag-ph').innerText = data.ph || "N/A";
        document.getElementById('diag-treatment').innerText = data.treatment || "Sin recomendaciones disponibles.";

        // (Opcional) Guardar el reporte en la bandeja de anomalías si viene crítico
        if (data.status && data.status.toLowerCase().includes('crítico') && typeof logPlantIssue === 'function') {
            logPlantIssue(data.species || "ESPECIE ESCANEADA", data.treatment);
        }

    } catch (error) {
        console.error("> [ ERROR CRÍTICO ] Error en conexión con el motor IA:", error);
        
        // Mensajes de error dentro de la UI para mantener la inmersión sin romper el flujo
        document.getElementById('diag-species').innerText = "ERROR DE CONEXIÓN";
        document.getElementById('diag-status').innerText = "Fallo al contactar servidor de visión.";
        document.getElementById('diag-ph').innerText = "ERR";
        document.getElementById('diag-treatment').innerText = "Reintente la conexión o verifique la red del clúster central.";
        
    } finally {
        // 5. Transición de Carga -> Resultado
        if (loadingModal) loadingModal.classList.add('hidden');
        const resultModal = document.getElementById('diagnosis-result-modal');
        if (resultModal) resultModal.classList.remove('hidden');
        
        // Reset del input para permitir nuevas capturas de inmediato
        const cameraInput = document.getElementById('camera-input');
        if (cameraInput) cameraInput.value = '';
    }
}

/**
 * CIERRE DE INTERFAZ DE DIAGNÓSTICO
 */
function closeDiagnosisModal() {
    const modal = document.getElementById('diagnosis-result-modal');
    if (modal) modal.classList.add('hidden');
}

/**
 * LISTENER INICIALIZADOR
 */
document.addEventListener('DOMContentLoaded', () => {
    const camInput = document.getElementById('camera-input');
    if (camInput) {
        camInput.addEventListener('change', handleImageUpload);
    }
});