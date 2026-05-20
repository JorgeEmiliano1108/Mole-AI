// ==========================================================
// FE-03: HardwareBinding inline panel for view-iot
// Renders a persistent table of active bindings + assignment form
// ==========================================================
import { getAuthToken } from '../api/config.js';

let _bindingsInitialized = false;

export function initBindingsPanel() {
    const container = document.getElementById('bindings-panel');
    if (!container) return;

    const deviceId = window.MoleState?.currentDeviceId || localStorage.getItem('moleia_device_id');
    if (!deviceId) {
        // PATCH-02: Do NOT set _bindingsInitialized here so re-navigation retries
        _bindingsInitialized = false;
        container.innerHTML = '<p class="text-mole-dim text-xs font-mono text-center py-6">[ SELECCIONE UN DISPOSITIVO ]</p>';
        return;
    }

    if (_bindingsInitialized) return;
    _bindingsInitialized = true;

    loadBindings(deviceId);
    wireForm(deviceId);
}

// PATCH-02: Allow external re-trigger after device linking
export function resetBindingsPanel() {
    _bindingsInitialized = false;
}

async function loadBindings(deviceId) {
    const tableBody = document.getElementById('bindings-table-body');
    const countEl   = document.getElementById('bindings-count');
    if (!tableBody) return;

    const token = getAuthToken();
    if (!token) return;

    try {
        const res = await fetch(
            `${window.AppConfig.API_BASE_URL}devices/${deviceId}/bindings/`,
            { headers: { 'Authorization': `Bearer ${token}` } }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const bindings = data.bindings || [];

        if (countEl) countEl.textContent = bindings.length;

        if (bindings.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-mole-dim text-xs py-6 font-mono">
                        [ SIN BINDINGS ACTIVOS ]
                    </td>
                </tr>`;
            return;
        }

        tableBody.innerHTML = bindings.map(b => `
            <tr class="border-b border-mole-border/30 hover:bg-mole-bg/50 transition-colors">
                <td class="py-2 px-2 text-mole-cyan font-mono text-xs">${b.hardware_pin}</td>
                <td class="py-2 px-2 text-mole-text text-xs">${b.plant_nickname || '--'}</td>
                <td class="py-2 px-2 text-mole-green text-[10px] italic font-mono">${b.species || '--'}</td>
                <td class="py-2 px-2 text-right">
                    <button
                        data-action="binding:delete"
                        data-binding-id="${b.id}"
                        data-device-id="${deviceId}"
                        class="text-mole-red hover:text-mole-red/70 text-[10px] font-bold tracking-wider px-2 py-1 border border-mole-red/30 rounded hover:bg-mole-red/10 transition-colors"
                    >[DESVINCULAR]</button>
                </td>
            </tr>`).join('');
    } catch (e) {
        console.error('[Bindings] Load failed:', e.message);
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-mole-red text-xs py-4 font-mono">
                    ERROR AL CARGAR BINDINGS
                </td>
            </tr>`;
    }
}

function wireForm(deviceId) {
    const form    = document.getElementById('binding-form');
    const pinIn   = document.getElementById('binding-pin');
    const plantIn = document.getElementById('binding-plant-id');
    const status  = document.getElementById('binding-status');

    if (!form || form.dataset.wired) return;
    form.dataset.wired = '1';

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const pin     = (pinIn?.value || '').trim();
        const plantId = (plantIn?.value || '').trim();

        if (!pin || !plantId) {
            showStatus(status, 'PIN y PLANT_ID son requeridos.', 'error');
            return;
        }

        const token = getAuthToken();
        if (!token) return;

        try {
            const res = await fetch(
                `${window.AppConfig.API_BASE_URL}devices/${deviceId}/bindings/`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ hardware_pin: pin, plant_id: plantId }),
                }
            );
            const data = await res.json();

            if (!res.ok) {
                showStatus(status, data.error || 'Error al crear binding.', 'error');
                return;
            }

            showStatus(status, `Binding creado: Pin ${data.hardware_pin}`, 'success');
            if (pinIn) pinIn.value = '';
            if (plantIn) plantIn.value = '';
            loadBindings(deviceId);
        } catch (e) {
            showStatus(status, 'Error de red.', 'error');
        }
    });
}

function showStatus(el, msg, type) {
    if (!el) return;
    el.classList.remove('hidden', 'text-mole-cyan', 'text-mole-red', 'text-mole-green');
    el.classList.add(type === 'error' ? 'text-mole-red' : 'text-mole-green');
    el.textContent = `> ${msg}`;
    setTimeout(() => el.classList.add('hidden'), 5000);
}

// Delete handler (registered in ActionMap)
export async function deleteBinding(bindingId, deviceId) {
    const token = getAuthToken();
    if (!token) return;

    try {
        const res = await fetch(
            `${window.AppConfig.API_BASE_URL}devices/${deviceId}/bindings/${bindingId}/`,
            {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` },
            }
        );
        if (res.status === 204 || res.ok) {
            loadBindings(deviceId);
        } else {
            console.error('[Bindings] Delete failed:', res.status);
        }
    } catch (e) {
        console.error('[Bindings] Delete error:', e.message);
    }
}
