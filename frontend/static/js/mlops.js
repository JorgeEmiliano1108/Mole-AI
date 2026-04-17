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

        await withBackoff(async () => {
            const response = await fetch(`${window.AppConfig.API_BASE_URL}/ai/rag/train/`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${window.getAuthToken()}` },
                body: formData
            });
            if (!response.ok) {
                const err = new Error("Error en servidor");
                err.status = response.status;
                throw err;
            }
        });
        
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

        await withBackoff(async () => {
            const response = await fetch(`${window.AppConfig.API_BASE_URL}/ai/vision/retrain/`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${window.getAuthToken()}` },
                body: formData
            });
            if (!response.ok) {
                const err = new Error("Error en servidor");
                err.status = response.status;
                throw err;
            }
        });
        
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
    const user = prompt("Ingrese su usuario o correo para recuperar la credencial:");
    if (!user) return;

    try {
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/auth/password-reset/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier: user })
        });

        if (response.ok) {
            alert("> PROTOCOLO DE RECUPERACIÓN INICIADO. Revise su terminal (correo).");
        } else {
            alert("> [ ERROR ] Credencial no encontrada o sistema bloqueado.");
        }
    } catch (e) {
        alert("> [ ERROR CRÍTICO ] No se pudo contactar al servidor central.");
    }
}