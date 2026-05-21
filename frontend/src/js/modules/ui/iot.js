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
    
    // Reset modal state
    const setupInstructions = document.getElementById('iot-setup-instructions');
    const wifiCredentials = document.getElementById('iot-wifi-credentials');
    if (setupInstructions) setupInstructions.classList.remove('hidden');
    if (wifiCredentials) wifiCredentials.classList.add('hidden');
    
    const wizardTitle = document.querySelector('#iot-wizard-modal h2');
    if (wizardTitle) {
        wizardTitle.innerText = `> ENLACE DE HARDWARE: ESP32_NODE`;
        wizardTitle.classList.remove('text-mole-green', 'text-mole-red');
        wizardTitle.classList.add('text-mole-accent');
    }
    
    // Wire scan button
    const btnScan = document.getElementById('btn-scan-esp');
    if (btnScan && !btnScan.dataset.wired) {
        btnScan.dataset.wired = '1';
        btnScan.addEventListener('click', async () => {
            btnScan.disabled = true;
            btnScan.textContent = 'ESCANEANDO RED LOCAL...';
            const success = await scanLocalEsp32();
            btnScan.disabled = false;
            btnScan.textContent = 'CONFIRMAR CONEXIÓN Y ESCANEAR';
            
            if (success) {
                if (setupInstructions) setupInstructions.classList.add('hidden');
                if (wifiCredentials) wifiCredentials.classList.remove('hidden');
            }
        });
    }
    
    console.log("> Iniciando protocolo de enlace IoT...");
}

/**
 * ESCANEO LOCAL (AP MODE / CAPTIVE PORTAL)
 * Intenta contactar al ESP32 en su IP de Gateway por defecto (192.168.4.1)
 * para verificar si el usuario está conectado a la red "Mole_OpenClaw".
 */
export async function scanLocalEsp32() {
    console.log("> [SCAN] Buscando dispositivo ESP32 en red local (192.168.4.1)...");
    try {
        // Hacemos una petición rápida al gateway del ESP32
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3s timeout
        
        // Asumiendo que el ESP32 en modo AP responde a /status o /info
        const response = await fetch('http://192.168.4.1/status', {
            method: 'GET',
            mode: 'cors',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            console.log("> [SCAN OK] ESP32 Encontrado:", data);
            // Mostrar indicación visual en la UI
            const wizardTitle = document.querySelector('#iot-wizard-modal h2');
            if (wizardTitle) {
                wizardTitle.innerText = `> ENLACE DE HARDWARE: ${data.node_id || 'ESP32_NODE'} [ONLINE]`;
                wizardTitle.classList.add('text-mole-green');
                wizardTitle.classList.remove('text-mole-accent', 'text-mole-red');
            }
            return true;
        }
        return false;
    } catch (error) {
        console.warn("> [SCAN WARN] No se detectó ESP32 en 192.168.4.1. ¿Está conectado al Captive Portal?", error.message);
        // Fallback visual
        const wizardTitle = document.querySelector('#iot-wizard-modal h2');
        if (wizardTitle) {
            wizardTitle.innerText = `> ENLACE DE HARDWARE: ESP32_NODE [OFFLINE]`;
            wizardTitle.classList.add('text-mole-red');
            wizardTitle.classList.remove('text-mole-accent', 'text-mole-green');
        }
        return false;
    }
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

        // Uso de la constante API_BASE_URL para despliegues reales
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/api/iot/provisioning`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.getAuthToken()}` 
            },
            body: JSON.stringify({ 
                ssid: ssid, 
                pass: password, 
                operator: currentUser
            })
        });

        if (!response.ok) throw new Error(`Fallo en el enlace de hardware. Código: ${response.status}`);

        await new Promise(resolve => setTimeout(resolve, 1500));

        nextIotStep(5);
        console.log("> [ OK ] Módulo ESP32 enlazado exitosamente.");

    } catch (error) {
        console.error("> [ ERROR CRÍTICO ] Falla de aprovisionamiento:", error);
        alert("[!] PROTOCOLO ABORTADO: No se pudo enlazar con el módulo de hardware. Verifique conexión.");
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