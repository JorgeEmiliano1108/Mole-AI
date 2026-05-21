// ==========================================================
// 14. MÓDULO IOT (ESP32) – NUEVO FLUJO DE WIZARD
// ==========================================================

/**
 * Show the IoT wizard modal and start at step 1.
 */
export function openIotWizard() {
  const modal = document.getElementById('iot-wizard-modal');
  if (!modal) return;
  modal.classList.remove('hidden');

  // Ensure we begin at the first step
  showIotStep(1);

  // Wire UI actions (only once)
  const btnStart = document.getElementById('btn-start-scan');
  if (btnStart && !btnStart.dataset.wired) {
    btnStart.dataset.wired = '1';
    btnStart.addEventListener('click', async () => {
      showIotStep(2);
      await pingEsp32(); // non‑blocking async ping
    });
  }

  const btnPing = document.getElementById('btn-ping');
  if (btnPing && !btnPing.dataset.wired) {
    btnPing.dataset.wired = '1';
    btnPing.addEventListener('click', async () => await pingEsp32());
  }

  const btnProvision = document.getElementById('btn-start-provision');
  if (btnProvision && !btnProvision.dataset.wired) {
    btnProvision.dataset.wired = '1';
    btnProvision.addEventListener('click', async () => {
      // Reuse existing provisioning logic (unchanged)
      await startHardwareProvisioning();
    });
  }

  console.log('> IoT Wizard abierto – paso 1 listo');
}

/** Helper: display only the requested step */
function showIotStep(stepNumber) {
  document.querySelectorAll('.iot-step').forEach(el => el.classList.add('hidden'));
  const target = document.getElementById(`iot-step-${stepNumber}`);
  if (target) target.classList.remove('hidden');
}

/** Async ping to the ESP32 captive‑portal (192.168.4.1) */
async function pingEsp32() {
  const statusSpan = document.getElementById('ping-status');
  const btnPing    = document.getElementById('btn-ping');

  if (statusSpan) statusSpan.textContent = '🔄 Enviando ping…';
  if (btnPing) btnPing.disabled = true;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 s timeout

    const response = await fetch('http://192.168.4.1/status', {
      method: 'GET',
      mode: 'cors',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json(); // does not block UI thread

    if (statusSpan) statusSpan.textContent = '✅ ESP32 encontrado';
    // Advance to credentials step
    showIotStep(3);
  } catch (err) {
    console.warn('[IoT Wizard] Ping falló:', err);
    if (statusSpan) statusSpan.textContent = '❌ No se detectó ESP32. Verifique la red.';
    if (btnPing) btnPing.disabled = false; // allow retry
  }
}

/** Close the wizard and clean any sensitive fields */
export function closeIotWizard() {
  const modal = document.getElementById('iot-wizard-modal');
  if (modal) modal.classList.add('hidden');
  // Clean credentials
  const ssidInput = document.getElementById('wifi-ssid');
  const passInput = document.getElementById('wifi-pass');
  if (ssidInput) ssidInput.value = '';
  if (passInput) {
    passInput.value = '';
    passInput.type = 'password';
  }
  console.log('> Wizard cerrado y credenciales purgadas');
}

/** Toggle password visibility – retained for UI */
export function toggleWifiPassword() {
  const passInput = document.getElementById('wifi-pass');
  if (!passInput) return;
  passInput.type = passInput.type === 'password' ? 'text' : 'password';
}

/**
 * APROVISIONAMIENTO DE HARDWARE (Conexión a Producción)
 * This function is unchanged apart from being called from the new step‑3 button.
 */
async function startHardwareProvisioning() {
  // Re‑use the existing provisioning implementation from the original file
  const ssid = document.getElementById('wifi-ssid')?.value;
  const password = document.getElementById('wifi-pass')?.value;
  const currentUser = localStorage.getItem('moleia_current_user') || 'ANONYMOUS';
  const token = window.getAuthToken();

  try {
    if (!token) throw new Error('Autorización denegada. Token de seguridad faltante.');
    console.log('> Transmitiendo credenciales al servidor central de producción...');
    const response = await fetch(`${window.AppConfig.API_BASE_URL}/api/iot/provisioning`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ ssid, pass: password, operator: currentUser }),
    });
    if (!response.ok) throw new Error(`Fallo en el enlace de hardware. Código: ${response.status}`);
    await new Promise(r => setTimeout(r, 1500));
    console.log('> [ OK ] Módulo ESP32 enlazado exitosamente.');
    // Optionally advance to a success view or close the wizard here
    closeIotWizard();
  } catch (e) {
    console.error('> [ ERROR ] Provisionamiento fallido:', e);
    alert('[!] PROTOCOLO ABORTADO: No se pudo enlazar con el módulo de hardware. Verifique conexión.');
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