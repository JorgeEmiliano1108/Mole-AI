// ==========================================================
// ISSUE-04: Device Health — Polling + Dual View (Botánico / SRE)
// ==========================================================
import { getAuthToken } from '../api/config.js';

const HEALTH_POLL_INTERVAL = 30_000; // 30 seconds
const LS_VIEW_MODE_KEY = 'moleia_health_view_mode';

let pollTimer = null;
let currentDeviceId = null;

// ── Public API ──────────────────────────────────────────────

export function initHealthView() {
    // Restore persisted view mode
    const saved = localStorage.getItem(LS_VIEW_MODE_KEY) || 'botanico';
    setViewMode(saved);

    // Wire toggle buttons
    const btnBot = document.getElementById('health-toggle-botanico');
    const btnSre = document.getElementById('health-toggle-sre');
    if (btnBot) btnBot.addEventListener('click', () => setViewMode('botanico'));
    if (btnSre) btnSre.addEventListener('click', () => setViewMode('sre'));

    // Start polling — uses a placeholder device ID until real selection exists
    // TODO: Replace with actual device selector when IoTNode ↔ User FK is unified
    currentDeviceId = localStorage.getItem('moleia_device_id') || null;
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
        
        // Show toggle if we have data
        const toggleContainer = document.getElementById('health-toggle-container');
        if (toggleContainer) toggleContainer.classList.remove('hidden');

        renderBotanico(data);
        renderSre(data);
        renderStatusOverlay(data);
    } catch (err) {
        console.warn('[Health] Fetch failed:', err.message);
    }
}

// ── Renderers ───────────────────────────────────────────────

function renderPlaceholder() {
    const panelBot = document.getElementById('health-panel-botanico');
    const panelSre = document.getElementById('health-panel-sre');
    const toggle   = document.getElementById('health-toggle-container');
    const overlay  = document.getElementById('health-offline-overlay');

    if (toggle) toggle.classList.add('hidden');
    if (overlay) overlay.classList.add('hidden');

    const html = `<div class="flex flex-col items-center justify-center h-48 text-mole-dim font-mono text-sm opacity-50">
        <span class="animate-pulse mb-2">[AWAIT]</span>
        <span>Esperando enlace de hardware...</span>
    </div>`;
    
    if (panelBot) panelBot.innerHTML = html;
    if (panelSre) panelSre.innerHTML = html;
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
