// ==========================================================
// MÓDULO DE MACHINE LEARNING OPERATIONS (MLOps) & SEGURIDAD
// ==========================================================

// Helper para Exponential Backoff en caso de Error 429 (Too Many Requests)
async function withBackoff(fn, maxRetries = 3) {
    let attempt = 0;
    while (attempt < maxRetries) {
        try {
            return await fn();
        } catch (error) {
            if (error.status === 429) {
                attempt++;
                const delay = Math.pow(2, attempt) * 1000;
                console.warn(`[!] Limitador de tasa activado (429). Reintentando en ${delay}ms...`);
                if (window.ApiService) ApiService.showToast(`Servidor ocupado. Reintentando en ${delay/1000}s...`, 'warn');
                await new Promise(resolve => setTimeout(resolve, delay));
            } else {
                throw error;
            }
        }
    }
    throw new Error("Límite de reintentos superado.");
}

async function trainRagModel() {
    const fileInput = document.getElementById('mlops-rag-file');
    if (!fileInput || !fileInput.files[0]) {
        if (window.ApiService) ApiService.showToast('Seleccione un documento primero.', 'error');
        return;
    }
    const btn = document.getElementById('btn-train-rag');
    btn.innerText = "[ ENVIANDO... ]";
    btn.classList.add('animate-pulse');

    try {
        const formData = new FormData();
        formData.append('document', fileInput.files[0]);

        await window.moleApi.upload('ai/rag/train/', formData, { silent: true });
        
        if (window.ApiService) ApiService.showToast('Base de Conocimiento RAG actualizada.', 'success');
        fileInput.value = '';
    } catch (e) {
        if (window.ApiService) ApiService.showToast('Fallo al contactar el MS2 (RAG).', 'error');
    } finally {
        btn.innerText = "[ ALIMENTAR RAG ]";
        btn.classList.remove('animate-pulse');
    }
}

async function trainCnnModel() {
    const fileInput = document.getElementById('mlops-cnn-file');
    if (!fileInput || !fileInput.files[0]) {
        if (window.ApiService) ApiService.showToast('Seleccione un dataset ZIP primero.', 'error');
        return;
    }
    const btn = document.getElementById('btn-train-cnn');
    btn.innerText = "[ PROCESANDO... ]";
    btn.classList.add('animate-pulse');

    try {
        const formData = new FormData();
        formData.append('dataset', fileInput.files[0]);

        await window.moleApi.upload('ai/vision/retrain/', formData, { silent: true });
        
        if (window.ApiService) ApiService.showToast('Fine-Tuning de MS1 iniciado. Revise los logs.', 'success');
        fileInput.value = '';
    } catch (e) {
        if (window.ApiService) ApiService.showToast('Fallo al iniciar reentrenamiento CNN.', 'error');
    } finally {
        btn.innerText = "[ INICIAR FINE-TUNING ]";
        btn.classList.remove('animate-pulse');
    }
}

async function forgotPassword() {
    // Usar el campo de usuario del formulario de login en lugar de prompt()
    const userInput = document.getElementById('user-input');
    const user = userInput ? userInput.value.trim() : '';
    if (!user) {
        if (window.showTacticalToast) window.showTacticalToast('Ingresa tu usuario para recuperar la credencial.', 'warn');
        return;
    }

    try {
        await window.moleApi.post('auth/password-reset/', { identifier: user }, { silent: true, allowAnonymous: true });
        if (window.showTacticalToast) window.showTacticalToast('Protocolo de recuperación iniciado. Revisa tu correo.', 'success');
    } catch (e) {
        if (e.status === 404) {
            if (window.showTacticalToast) window.showTacticalToast('Credencial no encontrada en el sistema.', 'error');
        } else {
            if (window.showTacticalToast) window.showTacticalToast('No se pudo contactar al servidor central.', 'error');
        }
    }
}