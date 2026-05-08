// ==========================================================
// 14. MÓDULO IOT (ESP32) Y PERFIL DE OPERADOR [PRODUCCIÓN READY]
// ==========================================================

// Definimos la URL base del servidor (esto idealmente viviría en tu Módulo 2 de variables globales)
// Use centralized AppConfig for API base URL (see static/js/config.js)
// Avoid redeclaring API_BASE_URL in multiple modules.
// Access via: window.AppConfig.API_BASE_URL

export function openIotWizard() {
    const modal = document.getElementById('iot-wizard-modal');
    if (!modal) return;
    
    modal.classList.remove('hidden');
    nextIotStep(1);
    console.log("> Iniciando protocolo de enlace IoT...");
}

export function closeIotWizard() {
    const modal = document.getElementById('iot-wizard-modal');
    if (modal) modal.classList.add('hidden');
    
    // [!] SEGURIDAD CRÍTICA: Limpiar contraseñas del DOM al cerrar
    const ssidInput = document.getElementById('wifi-ssid');
    const passInput = document.getElementById('wifi-pass');
    
    if (ssidInput) ssidInput.value = '';
    if (passInput) {
        passInput.value = '';
        passInput.type = 'password'; 
    }
    console.log("> Buffer de credenciales Wi-Fi purgado por seguridad.");
}

export function nextIotStep(stepNumber) {
    document.querySelectorAll('.iot-step').forEach(el => el.classList.add('hidden'));
    
    const targetStep = document.getElementById(`iot-step-${stepNumber}`);
    if (targetStep) targetStep.classList.remove('hidden');

    if (stepNumber === 3) {
        const ssidValue = document.getElementById('wifi-ssid')?.value || 'RED_DESCONOCIDA';
        const confirmSsid = document.getElementById('confirm-ssid');
        if (confirmSsid) confirmSsid.textContent = ssidValue;
    }
}

export function toggleWifiPassword() {
    const passInput = document.getElementById('wifi-pass');
    if (!passInput) return;
    passInput.type = passInput.type === 'password' ? 'text' : 'password';
}

/**
 * APROVISIONAMIENTO DE HARDWARE (Conexión a Producción)
 */
async function startHardwareProvisioning() {
    nextIotStep(4);
    const closeBtn = document.getElementById('iot-close-btn');
    if (closeBtn) closeBtn.classList.add('hidden'); 

    const ssid = document.getElementById('wifi-ssid')?.value;
    const password = document.getElementById('wifi-pass')?.value;
    const currentUser = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
    const token = window.getAuthToken();

    try {
        if (!token) throw new Error("Autorización denegada. Token de seguridad faltante.");
        console.log(`> Transmitiendo credenciales al servidor central de producción...`);

        await window.moleApi.post('api/iot/provisioning', {
            ssid: ssid,
            pass: password,
            operator: currentUser
        }, { silent: true });

        await new Promise(resolve => setTimeout(resolve, 1500));

        nextIotStep(5);
        console.log("> [ OK ] Módulo ESP32 enlazado exitosamente.");

    } catch (error) {
        console.error("> [ ERROR CRÍTICO ] Falla de aprovisionamiento:", error);
        if (window.showTacticalToast) {
            window.showTacticalToast('Protocolo abortado: No se pudo enlazar con el módulo de hardware.', 'error');
        }
        nextIotStep(1);
    } finally {
        if (closeBtn) closeBtn.classList.remove('hidden');
        const passInputFinal = document.getElementById('wifi-pass');
        if (passInputFinal) passInputFinal.value = '';
    }
}

// ==========================================================
// GESTIÓN DEL PERFIL DE OPERADOR
// ==========================================================


export function closeUserProfile() {
    const modal = document.getElementById('user-profile-modal');
    if (modal) modal.classList.add('hidden');
}

export function openDeleteModal() {
    closeUserProfile(); 
    const deleteModal = document.getElementById('delete-account-modal');
    if (deleteModal) deleteModal.classList.remove('hidden');
    
    const deleteInput = document.getElementById('confirm-delete-input');
    if (deleteInput) {
        deleteInput.value = '';
        if (typeof checkDeleteWord === 'function') checkDeleteWord();
    }
}