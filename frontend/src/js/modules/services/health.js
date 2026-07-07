// ==========================================================
// ISSUE-04: Device Health - Polling + Dual View (Bot nico / SRE)
// ==========================================================
import { getAuthToken } from '../api/config.js';
import { el, safeRender } from '../ui/dom.js';
import { apiService } from '../api/ApiService.js';

function renderAmbientCard(label, value, valueClass) {
    return el('div', { className: 'bg-mole-bg border border-mole-border rounded p-2 text-center' },
        el('span', { className: 'text-[10px] text-mole-dim uppercase tracking-wider block mb-1' }, label),
        el('span', { className: `text-lg font-bold ${valueClass}` }, value)
    );
}

function renderSoilCard(s) {
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
    const humValue = hum != null ? hum.toFixed(1) + '%' : '--';

    const idealEl = idealMin != null
        ? el('span', { className: 'text-[9px] text-mole-dim block -mt-1' }, `Ideal: ${idealMin}–${idealMax}%`)
        : null;

    return el('div', { className: 'bg-mole-surface border border-mole-border/50 rounded p-3 shadow-cyber' },
        el('div', { className: 'flex justify-between items-center mb-2' },
            el('div', {},
                el('span', { className: 'text-xs font-bold text-mole-cyan' }, s.plant_nickname || 'Sin Nombre'),
                el('span', { className: 'text-[9px] text-mole-dim font-mono ml-2' }, `PIN: ${s.pin}`)
            ),
            el('span', { className: 'text-[10px] text-mole-green italic' }, s.species || '--')
        ),
        el('div', { className: 'flex items-center justify-between bg-mole-bg rounded p-2' },
            el('span', { className: 'text-[10px] text-mole-dim uppercase tracking-wider' }, 'Humedad Suelo'),
            el('div', { className: 'text-right' },
                el('span', { className: `text-base font-bold ${humColors[humStatus]}` }, humValue),
                idealEl
            )
        )
    );
}

function renderSreSoilRow(s) {
    return el('tr', { className: 'border-b border-mole-border/10' },
        el('td', { className: 'py-1 text-mole-cyan' }, s.pin),
        el('td', { className: 'py-1 text-emerald-400 text-right' },
            s.soil_humidity != null ? s.soil_humidity.toFixed(1) + '%' : 'null'
        ),
        el('td', { className: 'py-1 text-mole-dim text-right hidden md:table-cell text-[8px]' },
            s.recorded_at ? new Date(s.recorded_at).toLocaleTimeString() : '--'
        )
    );
}

function renderSreInfoRow(label, value) {
    return el('tr', { className: 'border-b border-mole-border/30' },
        el('td', { className: 'py-1 text-mole-dim' }, label),
        el('td', { className: 'py-1 text-mole-cyan text-right' }, value)
    );
}

const HEALTH_POLL_INTERVAL = 30_000; // 30 seconds
const LS_VIEW_MODE_KEY = 'moleia_health_view_mode';

let pollTimer = null;
let currentDeviceId = null;

//    Public API                                               

let _healthInitialized = false;

window.addEventListener('userRoleReady', (e) => {
    const role = e.detail?.role || localStorage.getItem('moleia_user_role');
    const isSre = role === 'admin' || role === 'superuser';
    
    // UI Cleanup: Force hide SRE toggles if not SRE
    const toggleContainer = document.getElementById('health-toggle-container');
    if (!isSre && toggleContainer) {
        toggleContainer.classList.add('hidden'); // Tailwind hidden class
    }

    if (role === 'guest') {
        pausePolling();
        return;
    }

    if (!_healthInitialized) {
        initHealthView(isSre);
        _healthInitialized = true;
    }
});

export function initHealthView(isSre = false) {
    // Enforce bot nico view if not SRE
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

    const sectionContainer = document.getElementById('health-section-container');
    const toggleContainer = document.getElementById('health-toggle-container');
    if (!currentDeviceId) {
        if (sectionContainer) sectionContainer.classList.add('hidden');
        if (toggleContainer) toggleContainer.classList.add('hidden'); // hide toggles in zero state
    } else {
        if (sectionContainer) sectionContainer.classList.remove('hidden');
        if (toggleContainer) toggleContainer.classList.remove('hidden');
        fetchHealth();
        startPolling();
    }
}

export function setDeviceId(id) {
    currentDeviceId = id;
    const sectionContainer = document.getElementById('health-section-container');
    if (id) {
        localStorage.setItem('moleia_device_id', id);
        if (sectionContainer) sectionContainer.classList.remove('hidden');
        fetchHealth();
        startPolling();
    } else {
        localStorage.removeItem('moleia_device_id');
        if (sectionContainer) sectionContainer.classList.add('hidden');
        pausePolling();
    }
}

//    Internals                                                

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
        const fallbackToken = getAuthToken();
        if (fallbackToken) {
            try {
                const plantRes = await fetch(`${window.AppConfig.API_BASE_URL}plants/`, { 
                    headers: { 'Authorization': `Bearer ${fallbackToken}` } 
                });
                if (plantRes.ok) {
                    const plantData = await plantRes.json();
                    if (plantData.count > 0 && plantData.results) {
                        const mockData = {
                            status: 'offline',
                            device_id: 'NO VINCULADO',
                            device_name: 'REQUIERE BINDING',
                            last_seen_delta_seconds: null,
                            ambient: {},
                            soil: plantData.results.map(p => ({
                                plant_nickname: p.nickname || p.nombre || 'Planta',
                                pin: p.hardware_pin || '--',
                                species: p.species_id || 'Sin clasificar',
                                soil_humidity: null,
                                ideal_humidity_min: null,
                                ideal_humidity_max: null
                            }))
                        };
                        const toggleContainer = document.getElementById('health-toggle-container');
                        const role = localStorage.getItem('moleia_user_role');
                        const isSre = role === 'admin' || role === 'superuser';
                        if (toggleContainer) {
                            toggleContainer.classList.toggle('hidden', !isSre);
                            if (!isSre) toggleContainer.style.display = 'none';
                        }
                        
                        renderBotanico(mockData);
                        renderSre(mockData);
                        renderStatusOverlay(mockData);

                        const emptyState = document.getElementById('monitoreo-empty-state');
                        const kpiCards = document.getElementById('monitoreo-kpi-cards');
                        const panels = document.getElementById('monitoreo-panels');
                        if (emptyState) emptyState.classList.add('hidden');
                        if (kpiCards) kpiCards.classList.remove('hidden');
                        if (panels) panels.classList.remove('hidden');
                        return;
                    }
                }
            } catch (err) {
                console.warn('[Health] Fallback fetch failed:', err);
            }
        }

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

//    Renderers                                                

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
                // 1. Create plant mapped by name and physical hardware pin
                const plantRes = await apiService.post('plants/', { 
                    nickname: nickname,
                    hardware_pin: pin 
                });
                if (!plantRes || !plantRes.id) throw new Error("Fallo al crear la planta");

                // 2. If device is selected, also create the relational binding
                if (currentDeviceId) {
                    await apiService.post(`devices/${currentDeviceId}/bindings/`, {
                        hardware_pin: pin,
                        plant_id: plantRes.id
                    });
                    console.log("Hardware binding exitoso para dispositivo " + currentDeviceId);
                } else {
                    console.warn("Planta creada pero no hay deviceId para bindear.");
                    if (apiService && apiService.showToast) {
                        apiService.showToast("Planta registrada exitosamente. Ahora vincula tu nodo ESP32 desde el menú Wi-Fi.", "success");
                    } else {
                        alert("Planta registrada exitosamente. Recuerda vincular tu nodo ESP32 para iniciar el monitoreo.");
                    }
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
    const statusLabel = { online: 'SALUDABLE', warning: 'ATENCION', offline: 'SIN SE\u00d1AL' }[d.status] || 'DESCONOCIDO';

    let lastSeenStr = 'Sin datos';
    if (d.last_seen_delta_seconds !== null && d.last_seen_delta_seconds !== undefined) {
        const mins = Math.floor(d.last_seen_delta_seconds / 60);
        if (mins < 1) lastSeenStr = 'Hace unos segundos';
        else if (mins === 1) lastSeenStr = 'Hace 1 minuto';
        else if (mins < 60) lastSeenStr = `Hace ${mins} minutos`;
        else lastSeenStr = `Hace ${Math.floor(mins / 60)}h ${mins % 60}m`;
    }

    const amb = d.ambient || {};
    const soilData = d.soil || [];

    const soilCards = soilData.length === 0
        ? [el('div', { className: 'text-center text-mole-dim text-xs py-4 font-mono border border-dashed border-mole-border rounded' }, 'Sin pines configurados')]
        : soilData.map(function(s) { return renderSoilCard(s); });

    const soilContainer = soilData.length > 0
        ? el('div', { className: 'flex flex-col gap-3 overflow-y-auto max-h-[300px] pr-1' }, ...soilCards)
        : soilCards[0];

    const role = localStorage.getItem('moleia_user_role');
    const isSre = role === 'admin' || role === 'superuser';

    if (!isSre) {
        safeRender(panel,
            el('div', { className: 'flex flex-col items-center justify-center py-8' },
                el('span', { className: 'w-6 h-6 rounded-full mb-3 animate-pulse', style: { background: statusColor } }),
                el('span', { className: 'text-sm font-bold tracking-widest uppercase mb-2', style: { color: statusColor } }, statusLabel),
                el('span', { className: 'text-[10px] text-mole-dim font-mono mb-4' }, `NODO IOT: ${d.device_name || d.device_id}`),
                el('div', { className: 'flex gap-2' },
                    el('span', { className: 'text-[10px] text-mole-cyan font-mono border border-mole-cyan/30 px-3 py-1 rounded bg-mole-cyan/5' }, `SENSORES: ${soilData.length}`),
                    el('span', { className: 'text-[10px] text-mole-dim font-mono border border-mole-border px-3 py-1 rounded bg-mole-bg' }, lastSeenStr)
                )
            )
        );
        return;
    }

    safeRender(panel,
        el('div', { className: 'flex items-center justify-between mb-3' },
            el('div', { className: 'flex items-center gap-2' },
                el('span', { className: 'w-3 h-3 rounded-full animate-pulse', style: { background: statusColor } }),
                el('span', { className: 'text-xs font-bold tracking-widest uppercase', style: { color: statusColor } }, statusLabel)
            ),
            el('span', { className: 'text-[10px] text-mole-dim font-mono' }, lastSeenStr)
        ),
        el('div', { className: 'grid grid-cols-2 gap-2 mb-4' },
            renderAmbientCard('Temperatura', amb.air_temperature != null ? amb.air_temperature.toFixed(1) + ' C' : '--', 'text-orange-400'),
            renderAmbientCard('UV Index', amb.uv_index != null ? amb.uv_index : '--', 'text-violet-400')
        ),
        el('h3', { className: 'text-[10px] text-mole-accent font-bold uppercase tracking-wider mb-2 flex items-center gap-2' },
            el('span', { className: 'w-1 h-1 bg-mole-accent' }), ' LECTURAS POR CULTIVO'
        ),
        soilContainer
    );
}

function renderSre(d) {
    const panel = document.getElementById('health-panel-sre');
    if (!panel) return;

    const badgeColors = { online: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50', warning: 'bg-amber-500/20 text-amber-400 border-amber-500/50', offline: 'bg-red-500/20 text-red-400 border-red-500/50' };
    const badge = badgeColors[d.status] || badgeColors.offline;

    const soilData = d.soil || [];
    let soilTbody = el('tbody', {});
    if (soilData.length > 0) {
        soilData.forEach(function(s) { soilTbody.appendChild(renderSreSoilRow(s)); });
    }

    const soilTable = soilData.length > 0
        ? el('div', {},
            el('table', { className: 'w-full text-[10px] font-mono mt-1' },
                el('thead', {},
                    el('tr', { className: 'text-mole-dim border-b border-mole-border/30' },
                        el('th', { className: 'py-1 text-left font-normal' }, 'PIN'),
                        el('th', { className: 'py-1 text-right font-normal' }, 'HUM'),
                        el('th', { className: 'py-1 text-right font-normal hidden md:table-cell' }, 'TIME')
                    )
                ),
                soilTbody
            )
        )
        : el('div', { className: 'text-center text-mole-dim text-[10px] py-2 border border-dashed border-mole-border/50' }, 'Sin lecturas de suelo');

    safeRender(panel,
        el('div', { className: 'flex items-center justify-between mb-3' },
            el('span', { className: `text-xs font-bold px-2 py-1 rounded border ${badge} uppercase tracking-widest` }, d.status.toUpperCase()),
            el('span', { className: 'text-[10px] text-mole-dim font-mono' }, d.device_id)
        ),
        el('table', { className: 'w-full text-[11px] font-mono' },
            el('tbody', {},
                renderSreInfoRow('last_seen', d.last_seen || 'null'),
                renderSreInfoRow('delta_seconds', `${d.last_seen_delta_seconds}s`),
                renderSreInfoRow('uptime_24h', `${d.sre_metrics?.uptime_pct_24h ?? '--'}%`),
                renderSreInfoRow('ws_reconnects_24h', d.sre_metrics?.ws_reconnects_24h ?? '--')
            )
        ),
        el('div', { className: 'mt-3' },
            el('div', { className: 'px-2 py-1 bg-mole-bg text-[9px] text-mole-dim uppercase tracking-wider border border-mole-border/30 rounded-t flex justify-between' },
                el('span', {}, 'SOIL BINDINGS'),
                el('span', {}, `${soilData.length} ACTIVE`)
            ),
            el('div', { className: 'border-x border-b border-mole-border/30 px-2 py-1 rounded-b' },
                soilTable
            )
        ),
        el('div', { className: 'mt-3 border border-mole-border/30 rounded' },
            el('div', { className: 'px-2 py-1 bg-mole-bg text-[9px] text-mole-dim uppercase tracking-wider border-b border-mole-border/30' }, 'AMBIENT PAYLOAD'),
            el('pre', { className: 'px-2 py-1 text-[9px] text-mole-cyan font-mono overflow-x-auto' }, JSON.stringify(d.ambient || {}, null, 2))
        )
    );
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
