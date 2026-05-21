// ==========================================================
// ISSUE-04: Device Health — Polling + Dual View (Botánico / SRE)
// ==========================================================
import { getAuthToken } from '../api/config.js';

const HEALTH_POLL_INTERVAL = 30_000; // 30 seconds
const LS_VIEW_MODE_KEY = 'moleia_health_view_mode';

let pollTimer = null;
let currentDeviceId = null;

// ── Public API ──────────────────────────────────────────────

let _healthInitialized = false;

window.addEventListener('userRoleReady', (e) => {
    const role = e.detail?.role || localStorage.getItem('moleia_user_role');
    const isSre = role === 'admin' || role === 'superuser';
    
    // UI Cleanup: Force hide SRE toggles if not SRE
    const toggleContainer = document.getElementById('health-toggle-container');
    if (!isSre && toggleContainer) {
        toggleContainer.style.display = 'none'; // Hard hide
    }

    if (!_healthInitialized) {
        initHealthView(isSre);
        _healthInitialized = true;
    }
});

export function initHealthView(isSre = false) {
    // Enforce botánico view if not SRE
    const saved = isSre ? (localStorage.getItem(LS_VIEW_MODE_KEY) || 'botanico') : 'botanico';
    setViewMode(saved);

    // Wire toggle buttons
    const btnBot = document.getElementById('health-toggle-botanico');
    const btnSre = document.getElementById('health-toggle-sre');
    if (btnBot) {
        btnBot.replaceWith(btnBot.cloneNode(true));
        document.getElementById('health-toggle-botanico').addEventListener('click', () => setViewMode('botanico'));
    }
    if (btnSre && isSre) {
        btnSre.replaceWith(btnSre.cloneNode(true));
        document.getElementById('health-toggle-sre').addEventListener('click', () => setViewMode('sre'));
    }

    // Start polling
    currentDeviceId = localStorage.getItem('moleia_device_id') || null;

    // FE-09: Plant Registration setup
    setupPlantRegistration();

    if (currentDeviceId) {
        fetchHealth();
        startPolling();
    }
}

export function setDeviceId(id) {
    currentDeviceId = id;
    localStorage.setItem('moleia_device_id', id);
    fetchHealth();
    startPolling();
}

// ── Internals ───────────────────────────────────────────────

function startPolling() {
    stopPolling();
    // FE-05: Only start polling if we have a valid device
    if (!currentDeviceId) return;
    pollTimer = setInterval(fetchHealth, HEALTH_POLL_INTERVAL);
}

function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

// Public polling control for view lifecycle management (FE-01)
export function pausePolling() {
    stopPolling();
}

export function resumePolling() {
    if (currentDeviceId && !pollTimer) {
        fetchHealth();
        startPolling();
    }
}

function setViewMode(mode) {
    const role = localStorage.getItem('moleia_user_role');
    const isSre = role === 'admin' || role === 'superuser';
    if (!isSre) mode = 'botanico'; // Force botanico for non-admins

    localStorage.setItem(LS_VIEW_MODE_KEY, mode);

    const btnBot = document.getElementById('health-toggle-botanico');
    const btnSre = document.getElementById('health-toggle-sre');
    const panelBot = document.getElementById('health-panel-botanico');
    const panelSre = document.getElementById('health-panel-sre');

    if (mode === 'sre') {
        btnBot?.classList.remove('bg-mole-cyan', 'text-mole-base');
        btnBot?.classList.add('bg-mole-surface', 'text-mole-dim');
        btnSre?.classList.add('bg-mole-cyan', 'text-mole-base');
        btnSre?.classList.remove('bg-mole-surface', 'text-mole-dim');
        panelBot?.classList.add('hidden');
        panelSre?.classList.remove('hidden');
    } else {
        btnSre?.classList.remove('bg-mole-cyan', 'text-mole-base');
        btnSre?.classList.add('bg-mole-surface', 'text-mole-dim');
        btnBot?.classList.add('bg-mole-cyan', 'text-mole-base');
        btnBot?.classList.remove('bg-mole-surface', 'text-mole-dim');
        panelSre?.classList.add('hidden');
        panelBot?.classList.remove('hidden');
    }
}

async function fetchHealth() {
    // FE-05: Guard
    if (!currentDeviceId) {
        renderPlaceholder();
        return;
    }

    const token = getAuthToken();
    if (!token) return;

    try {
        const res = await fetch(
            `${window.AppConfig.API_BASE_URL}devices/${currentDeviceId}/health/`,
            { headers: { 'Authorization': `Bearer ${token}` } }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        // Fetch everything, backend determines what data it sends based on token.
        // We handle UI visibility below based on role.
        const toggleContainer = document.getElementById('health-toggle-container');
        const role = localStorage.getItem('moleia_user_role');
        const isSre = role === 'admin' || role === 'superuser';
        
        if (toggleContainer) {
            toggleContainer.classList.toggle('hidden', !isSre);
            if (!isSre) toggleContainer.style.display = 'none'; // Ensure hidden
        }

        renderBotanico(data);
        renderSre(data);
        renderStatusOverlay(data);

        // FE-09: Show/hide empty state based on soil sensors
        const emptyState = document.getElementById('monitoreo-empty-state');
        const kpiCards = document.getElementById('monitoreo-kpi-cards');
        const panels = document.getElementById('monitoreo-panels');
        if (data.soil && data.soil.length > 0) {
            if (emptyState) emptyState.classList.add('hidden');
            if (kpiCards) kpiCards.classList.remove('hidden');
            if (panels) panels.classList.remove('hidden');
        } else {
            if (emptyState) emptyState.classList.remove('hidden');
            if (kpiCards) kpiCards.classList.add('hidden');
            if (panels) panels.classList.add('hidden');
        }

    } catch (err) {
        console.warn('[Health] Fetch failed:', err.message);
    }
}

// ── Renderers ───────────────────────────────────────────────

function renderPlaceholder() {
    const emptyState = document.getElementById('monitoreo-empty-state');
    const kpiCards = document.getElementById('monitoreo-kpi-cards');
    const panels = document.getElementById('monitoreo-panels');

    if (emptyState) emptyState.classList.remove('hidden');
    if (kpiCards) kpiCards.classList.add('hidden');
    if (panels) panels.classList.add('hidden');
}

// -- FE-09: Plant Registration Logic -----------------------------
function setupPlantRegistration() {
    const btnAdd = document.getElementById('btn-add-plant');
    const btnCancel = document.getElementById('btn-cancel-reg');
    const formReg = document.getElementById('form-register-plant');

    if (btnAdd) {
        btnAdd.addEventListener('click', () => {
            btnAdd.classList.add('hidden');
            btnAdd.nextElementSibling.classList.add('hidden'); // text
            if (formReg) formReg.classList.remove('hidden');
        });
    }

    if (btnCancel) {
        btnCancel.addEventListener('click', () => {
            if (formReg) formReg.classList.add('hidden');
            if (btnAdd) {
                btnAdd.classList.remove('hidden');
                btnAdd.nextElementSibling.classList.remove('hidden');
            }
        });
    }

    if (formReg) {
        formReg.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nickname = document.getElementById('reg-plant-name')?.value;
            const pin = document.getElementById('reg-plant-pin')?.value;

            if (!nickname || !pin) return;

            const btnSubmit = formReg.querySelector('button[type="submit"]');
            const originalText = btnSubmit.textContent;
            btnSubmit.textContent = '...';
            btnSubmit.disabled = true;

            try {
                // 1. Create plant
                const plantRes = await window.ApiService.post('plants/', { nickname });
                if (!plantRes || !plantRes.id) throw new Error("Fallo al crear la planta");

                // 2. If device is selected, bind it
                if (currentDeviceId) {
                    await window.ApiService.post(`devices/${currentDeviceId}/bindings/`, {
                        hardware_pin: pin,
                        plant_id: plantRes.id
                    });
                    console.log("Hardware binding exitoso para dispositivo " + currentDeviceId);
                } else {
                    console.warn("Planta creada pero no hay deviceId para bindear.");
                }

                formReg.reset();
                if (btnCancel) btnCancel.click();
                fetchHealth(); // Refresh UI
            } catch (err) {
                console.error("Error registering plant / binding hardware:", err);
                if (err.status === 403 || err.message.includes('403')) {
                    alert("Permisos insuficientes para registrar datos.");
                } else {
                    alert("Error al registrar: " + (err.message || err));
                }
            } finally {
                btnSubmit.textContent = originalText;
                btnSubmit.disabled = false;
            }
        });
    }
}

function renderBotanico(d) {
    const panel = document.getElementById('health-panel-botanico');
    if (!panel) return;

    const statusColor = { online: '#22c55e', warning: '#f59e0b', offline: '#ef4444' }[d.status] || '#6b7280';
    const statusLabel = { online: 'SALUDABLE', warning: 'ATENCION', offline: 'SIN SEÑAL' }[d.status] || 'DESCONOCIDO';

    let lastSeenStr = 'Sin datos';
    if (d.last_seen_delta_seconds !== null && d.last_seen_delta_seconds !== undefined) {
        const mins = Math.floor(d.last_seen_delta_seconds / 60);
        if (mins < 1) lastSeenStr = 'Hace unos segundos';
        else if (mins === 1) lastSeenStr = 'Hace 1 minuto';
        else if (mins < 60) lastSeenStr = `Hace ${mins} minutos`;
        else lastSeenStr = `Hace ${Math.floor(mins / 60)}h ${mins % 60}m`;
    }

    // Ambiente global
    const amb = d.ambient || {};
    const ambientHtml = `
        <div class="grid grid-cols-2 gap-2 mb-4">
            <div class="bg-mole-bg border border-mole-border rounded p-2 text-center">
                <span class="text-[10px] text-mole-dim uppercase tracking-wider block mb-1">Temperatura</span>
                <span class="text-lg font-bold text-orange-400">${amb.air_temperature != null ? amb.air_temperature.toFixed(1) + ' C' : '--'}</span>
            </div>
            <div class="bg-mole-bg border border-mole-border rounded p-2 text-center">
                <span class="text-[10px] text-mole-dim uppercase tracking-wider block mb-1">UV Index</span>
                <span class="text-lg font-bold text-violet-400">${amb.uv_index != null ? amb.uv_index : '--'}</span>
            </div>
        </div>
    `;

    // FE-04: Iterate soil[] array for multi-pin view (Vertical Scroll - Q-FE-04-1)
    let soilHtml = '';
    const soilData = d.soil || [];

    if (soilData.length === 0) {
        soilHtml = `<div class="text-center text-mole-dim text-xs py-4 font-mono border border-dashed border-mole-border rounded">Sin pines configurados</div>`;
    } else {
        soilHtml = `<div class="flex flex-col gap-3 overflow-y-auto max-h-[300px] pr-1">`;

        soilData.forEach(s => {
            const hum = s.soil_humidity;
            const idealMin = s.ideal_humidity_min;
            const idealMax = s.ideal_humidity_max;

            let humStatus = 'neutral';
            if (hum != null && idealMin != null && idealMax != null) {
                if (hum >= idealMin && hum <= idealMax) humStatus = 'optimal';
                else if (hum < idealMin) humStatus = 'low';
                else humStatus = 'high';
            }
            const humColors = { optimal: 'text-emerald-400', low: 'text-sky-400', high: 'text-red-400', neutral: 'text-mole-dim' };

            soilHtml += `
                <div class="bg-mole-surface border border-mole-border/50 rounded p-3 shadow-cyber">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <span class="text-xs font-bold text-mole-cyan">${s.plant_nickname || 'Sin Nombre'}</span>
                            <span class="text-[9px] text-mole-dim font-mono ml-2">PIN: ${s.pin}</span>
                        </div>
                        <span class="text-[10px] text-mole-green italic">${s.species || '--'}</span>
                    </div>
                    <div class="flex items-center justify-between bg-mole-bg rounded p-2">
                        <span class="text-[10px] text-mole-dim uppercase tracking-wider">Humedad Suelo</span>
                        <div class="text-right">
                            <span class="text-base font-bold ${humColors[humStatus]}">${hum != null ? hum.toFixed(1) + '%' : '--'}</span>
                            ${idealMin != null ? `<span class="text-[9px] text-mole-dim block -mt-1">Ideal: ${idealMin}–${idealMax}%</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        soilHtml += `</div>`;
    }

    const role = localStorage.getItem('moleia_user_role');
    const isSre = role === 'admin' || role === 'superuser';

    if (!isSre) {
        panel.innerHTML = `
            <div class="flex flex-col items-center justify-center py-8">
                <span class="w-6 h-6 rounded-full mb-3 animate-pulse" style="background:${statusColor}"></span>
                <span class="text-sm font-bold tracking-widest uppercase mb-2" style="color:${statusColor}">${statusLabel}</span>
                <span class="text-[10px] text-mole-dim font-mono mb-4">NODO IOT: ${d.device_name || d.device_id}</span>
                <div class="flex gap-2">
                    <span class="text-[10px] text-mole-cyan font-mono border border-mole-cyan/30 px-3 py-1 rounded bg-mole-cyan/5">SENSORES: ${soilData.length}</span>
                    <span class="text-[10px] text-mole-dim font-mono border border-mole-border px-3 py-1 rounded bg-mole-bg">${lastSeenStr}</span>
                </div>
            </div>
        `;
        return;
    }

    panel.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full animate-pulse" style="background:${statusColor}"></span>
                <span class="text-xs font-bold tracking-widest uppercase" style="color:${statusColor}">${statusLabel}</span>
            </div>
            <span class="text-[10px] text-mole-dim font-mono">${lastSeenStr}</span>
        </div>
        ${ambientHtml}
        <h3 class="text-[10px] text-mole-accent font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
            <span class="w-1 h-1 bg-mole-accent"></span> LECTURAS POR CULTIVO
        </h3>
        ${soilHtml}
    `;
}

function renderSre(d) {
    const panel = document.getElementById('health-panel-sre');
    if (!panel) return;

    const badgeColors = { online: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50', warning: 'bg-amber-500/20 text-amber-400 border-amber-500/50', offline: 'bg-red-500/20 text-red-400 border-red-500/50' };
    const badge = badgeColors[d.status] || badgeColors.offline;

    const soilData = d.soil || [];
    let soilTable = `<div class="text-center text-mole-dim text-[10px] py-2 border border-dashed border-mole-border/50">Sin lecturas de suelo</div>`;

    if (soilData.length > 0) {
        soilTable = `
            <table class="w-full text-[10px] font-mono mt-1">
                <thead>
                    <tr class="text-mole-dim border-b border-mole-border/30">
                        <th class="py-1 text-left font-normal">PIN</th>
                        <th class="py-1 text-right font-normal">HUM</th>
                        <th class="py-1 text-right font-normal hidden md:table-cell">TIME</th>
                    </tr>
                </thead>
                <tbody>
                    ${soilData.map(s => `
                        <tr class="border-b border-mole-border/10">
                            <td class="py-1 text-mole-cyan">${s.pin}</td>
                            <td class="py-1 text-emerald-400 text-right">${s.soil_humidity != null ? s.soil_humidity.toFixed(1) + '%' : 'null'}</td>
                            <td class="py-1 text-mole-dim text-right hidden md:table-cell text-[8px]">${s.recorded_at ? new Date(s.recorded_at).toLocaleTimeString() : '--'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    panel.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold px-2 py-1 rounded border ${badge} uppercase tracking-widest">${d.status.toUpperCase()}</span>
            <span class="text-[10px] text-mole-dim font-mono">${d.device_id}</span>
        </div>
        <table class="w-full text-[11px] font-mono">
            <tbody>
                <tr class="border-b border-mole-border/30">
                    <td class="py-1 text-mole-dim">last_seen</td>
                    <td class="py-1 text-mole-cyan text-right">${d.last_seen || 'null'}</td>
                </tr>
                <tr class="border-b border-mole-border/30">
                    <td class="py-1 text-mole-dim">delta_seconds</td>
                    <td class="py-1 text-mole-cyan text-right">${d.last_seen_delta_seconds}s</td>
                </tr>
                <tr class="border-b border-mole-border/30">
                    <td class="py-1 text-mole-dim">uptime_24h</td>
                    <td class="py-1 text-mole-cyan text-right">${d.sre_metrics?.uptime_pct_24h ?? '--'}%</td>
                </tr>
                <tr class="border-b border-mole-border/30">
                    <td class="py-1 text-mole-dim">ws_reconnects_24h</td>
                    <td class="py-1 text-mole-cyan text-right">${d.sre_metrics?.ws_reconnects_24h ?? '--'}</td>
                </tr>
            </tbody>
        </table>
        
        <div class="mt-3">
            <div class="px-2 py-1 bg-mole-bg text-[9px] text-mole-dim uppercase tracking-wider border border-mole-border/30 rounded-t flex justify-between">
                <span>SOIL BINDINGS</span>
                <span>${soilData.length} ACTIVE</span>
            </div>
            <div class="border-x border-b border-mole-border/30 px-2 py-1 rounded-b">
                ${soilTable}
            </div>
        </div>
        
        <div class="mt-3 border border-mole-border/30 rounded">
            <div class="px-2 py-1 bg-mole-bg text-[9px] text-mole-dim uppercase tracking-wider border-b border-mole-border/30">AMBIENT PAYLOAD</div>
            <pre class="px-2 py-1 text-[9px] text-mole-cyan font-mono overflow-x-auto">${JSON.stringify(d.ambient || {}, null, 2)}</pre>
        </div>
    `;
}

function renderStatusOverlay(d) {
    const overlay = document.getElementById('health-offline-overlay');
    if (!overlay) return;

    if (d.status === 'offline') {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}
