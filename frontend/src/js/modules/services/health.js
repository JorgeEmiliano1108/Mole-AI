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
    pollTimer = setInterval(fetchHealth, HEALTH_POLL_INTERVAL);
}

function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
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
    if (!currentDeviceId) return;

    const token = getAuthToken();
    if (!token) return;

    try {
        const res = await fetch(
            `${window.AppConfig.API_BASE_URL}devices/${currentDeviceId}/health/`,
            { headers: { 'Authorization': `Bearer ${token}` } }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderBotanico(data);
        renderSre(data);
        renderStatusOverlay(data);
    } catch (err) {
        console.warn('[Health] Fetch failed:', err.message);
    }
}

// ── Renderers ───────────────────────────────────────────────

function renderBotanico(d) {
    const panel = document.getElementById('health-panel-botanico');
    if (!panel) return;

    const statusColor = { online: '#22c55e', warning: '#f59e0b', offline: '#ef4444' }[d.status] || '#6b7280';
    const statusLabel = { online: 'SALUDABLE', warning: 'ATENCIÓN', offline: 'SIN SEÑAL' }[d.status] || 'DESCONOCIDO';

    // Friendly "last seen" string
    let lastSeenStr = 'Sin datos';
    if (d.last_seen_delta_seconds !== null && d.last_seen_delta_seconds !== undefined) {
        const mins = Math.floor(d.last_seen_delta_seconds / 60);
        if (mins < 1) lastSeenStr = 'Hace unos segundos';
        else if (mins === 1) lastSeenStr = 'Hace 1 minuto';
        else if (mins < 60) lastSeenStr = `Hace ${mins} minutos`;
        else lastSeenStr = `Hace ${Math.floor(mins / 60)}h ${mins % 60}m`;
    }

    // Humidity gauge range
    const hum = d.latest_reading?.soil_humidity;
    const idealMin = d.plant?.ideal_humidity_min;
    const idealMax = d.plant?.ideal_humidity_max;
    let humStatus = 'neutral';
    if (hum !== null && hum !== undefined && idealMin != null && idealMax != null) {
        if (hum >= idealMin && hum <= idealMax) humStatus = 'optimal';
        else if (hum < idealMin) humStatus = 'low';
        else humStatus = 'high';
    }
    const humColors = { optimal: 'text-emerald-400', low: 'text-sky-400', high: 'text-red-400', neutral: 'text-mole-dim' };

    panel.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full animate-pulse" style="background:${statusColor}"></span>
                <span class="text-xs font-bold tracking-widest uppercase" style="color:${statusColor}">${statusLabel}</span>
            </div>
            <span class="text-[10px] text-mole-dim font-mono">${lastSeenStr}</span>
        </div>
        <div class="grid grid-cols-2 gap-2">
            <div class="bg-mole-bg border border-mole-border rounded p-2 text-center">
                <span class="text-[10px] text-mole-dim uppercase tracking-wider block mb-1">Humedad Suelo</span>
                <span class="text-lg font-bold ${humColors[humStatus]}">${hum != null ? hum.toFixed(1) + '%' : '--'}</span>
                ${idealMin != null ? `<span class="text-[9px] text-mole-dim block">Ideal: ${idealMin}–${idealMax}%</span>` : ''}
            </div>
            <div class="bg-mole-bg border border-mole-border rounded p-2 text-center">
                <span class="text-[10px] text-mole-dim uppercase tracking-wider block mb-1">Temperatura</span>
                <span class="text-lg font-bold text-orange-400">${d.latest_reading?.air_temperature != null ? d.latest_reading.air_temperature.toFixed(1) + '°C' : '--'}</span>
            </div>
            <div class="bg-mole-bg border border-mole-border rounded p-2 text-center">
                <span class="text-[10px] text-mole-dim uppercase tracking-wider block mb-1">pH</span>
                <span class="text-lg font-bold text-emerald-400">${d.latest_reading?.ph_level != null ? d.latest_reading.ph_level.toFixed(1) : '--'}</span>
                ${d.plant?.ideal_ph_min != null ? `<span class="text-[9px] text-mole-dim block">Ideal: ${d.plant.ideal_ph_min}–${d.plant.ideal_ph_max}</span>` : ''}
            </div>
            <div class="bg-mole-bg border border-mole-border rounded p-2 text-center">
                <span class="text-[10px] text-mole-dim uppercase tracking-wider block mb-1">UV</span>
                <span class="text-lg font-bold text-violet-400">${d.latest_reading?.uv_index != null ? d.latest_reading.uv_index : '--'}</span>
            </div>
        </div>
        ${d.plant?.species ? `<div class="mt-2 text-[10px] text-mole-dim font-mono text-center">Especie: <span class="text-mole-cyan italic">${d.plant.species}</span></div>` : ''}
    `;
}

function renderSre(d) {
    const panel = document.getElementById('health-panel-sre');
    if (!panel) return;

    const badgeColors = { online: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50', warning: 'bg-amber-500/20 text-amber-400 border-amber-500/50', offline: 'bg-red-500/20 text-red-400 border-red-500/50' };
    const badge = badgeColors[d.status] || badgeColors.offline;

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
        <div class="mt-3 border border-mole-border/30 rounded">
            <div class="px-2 py-1 bg-mole-bg text-[10px] text-mole-dim uppercase tracking-wider border-b border-mole-border/30">Raw Sensor Payload</div>
            <pre class="px-2 py-1 text-[10px] text-mole-cyan font-mono overflow-x-auto">${JSON.stringify(d.latest_reading, null, 2)}</pre>
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
