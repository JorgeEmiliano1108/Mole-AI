import { el, safeRender } from '../ui/dom.js';
import { apiService } from '../api/ApiService.js';
import { getAuthToken } from '../api/config.js';
import L from 'leaflet/dist/leaflet.js';
import 'leaflet/dist/leaflet.css';

// ==========================================================
// 10. FLUJO DE GEOLOCALIZACI N (MAPA Y PERMISOS) [BACKEND ESTRICTO]
// ==========================================================
// Leaflet (bundled via pnpm)

export let mapInstance = null;
export let userLocation = null;

// Grupos de capas GIS
export let layers = {
    base: null,
    temp: null,
    precip: null,
    plagas: null
};

// 1. Pedir permiso de ubicaci n EXACTA
export function requestLocation() {
    if ("geolocation" in navigator) {
        const opcionesGPS = { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 };
        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = { lat: position.coords.latitude, lng: position.coords.longitude };
                console.log("> UBICACI\u00d3N EXACTA CAPTURADA:", userLocation);
                if (mapInstance) {
                    mapInstance.setView([userLocation.lat, userLocation.lng], 16);
                }
            },
            (error) => console.warn("> ACCESO A GPS DENEGADO O FALLIDO:", error.message),
            opcionesGPS
        );
    }
}

// 2. Inicializar Mapa y Capas
export function initMapView() {
    console.log("[MAPA] Iniciando renderizado GIS...");
    const mapDiv = document.getElementById('map');
    if (!mapDiv) return;
    
    if (!mapInstance) {
        mapInstance = L.map('map').setView([23.6345, -102.5528], 5);

        // Base Ciberpunk (CartoDB Dark Matter)
        layers.base = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CARTO', subdomains: 'abcd', maxZoom: 20
        }).addTo(mapInstance);

        // Capas Clim ticas (Proxy Local)
        const baseUrl = window.AppConfig?.API_BASE_URL || '/api/v1/';
        
        layers.temp = L.tileLayer(`${baseUrl}weather/tile/temp_new/{z}/{x}/{y}.png`, {
            opacity: 0.6, maxZoom: 18, attribution: '&copy; OpenWeather'
        });
        
        layers.precip = L.tileLayer(`${baseUrl}weather/tile/precipitation_new/{z}/{x}/{y}.png`, {
            opacity: 0.6, maxZoom: 18, attribution: '&copy; OpenWeather'
        });

        // Capa de Vectores (Plagas)
        layers.plagas = L.layerGroup().addTo(mapInstance);

        // Vincular Controles UI Flotantes y Clics de Mapa
        setupLayerControls();
        setupMapInteractivity();
    }
    
    setTimeout(() => {
        if (mapInstance) {
            mapInstance.invalidateSize(true);
            loadMapPins();
        }
    }, 500);
}


function setupLayerControls() {
    const toggleButtonLayer = (btnId, layerObj, activeClass, inactiveClass) => {
        const btn = document.getElementById(btnId);
        if (!btn || !layerObj) return;
        
        // Estado inicial de la capa
        let isLayerActive = mapInstance.hasLayer(layerObj);

        btn.addEventListener('click', () => {
            isLayerActive = !isLayerActive;
            if (isLayerActive) {
                mapInstance.addLayer(layerObj);
                btn.className = activeClass;
            } else {
                mapInstance.removeLayer(layerObj);
                btn.className = inactiveClass;
            }
        });
    };

    // Clases comunes para el toggle de botones
    const baseBtnClass = "w-10 h-10 flex items-center justify-center rounded-lg transition-colors";
    
    const tempInactive = `${baseBtnClass} bg-mole-surface/80 text-mole-dim hover:bg-mole-bg hover:text-orange-500`;
    const tempActive = `${baseBtnClass} bg-mole-accent text-mole-base shadow-[0_0_10px_rgba(0,229,255,0.4)]`;
    
    const precipInactive = `${baseBtnClass} bg-mole-surface/80 text-mole-dim hover:bg-mole-bg hover:text-sky-500`;
    const precipActive = `${baseBtnClass} bg-mole-accent text-mole-base shadow-[0_0_10px_rgba(0,229,255,0.4)]`;

    const plagasInactive = `${baseBtnClass} bg-mole-surface/80 text-mole-dim hover:bg-mole-bg hover:text-mole-green`;
    const plagasActive = `${baseBtnClass} bg-mole-accent text-mole-base shadow-[0_0_10px_rgba(0,229,255,0.4)]`;

    toggleButtonLayer('btn-layer-temp', layers.temp, tempActive, tempInactive);
    toggleButtonLayer('btn-layer-precip', layers.precip, precipActive, precipInactive);
    toggleButtonLayer('btn-layer-plagas', layers.plagas, plagasActive, plagasInactive);
}

function setupMapInteractivity() {
    // 1. Clic en espacio vac o: Consultar clima actual
    mapInstance.on('click', async (e) => {
        const { lat, lng } = e.latlng;
        const panel = document.getElementById('map-info-panel');
        const title = document.getElementById('info-title');
        const content = document.getElementById('info-content');

        if (!panel || !title || !content) return;

        // Estado Loading
        panel.classList.remove('hidden');
        title.innerText = "CLIMA ACTUAL";
        safeRender(content,
            el('div', { className: 'text-mole-cyan animate-pulse' }, 'Obteniendo telemetr\u00eda orbital...')
        );

        try {
            const res = await apiService.get(`weather/current/?lat=${lat}&lon=${lng}`);
            if (res && res.main) {
                const temp = res.main.temp.toFixed(1);
                const humidity = res.main.humidity;
                const desc = res.weather[0]?.description || 'N/A';
                const city = res.name || 'Coordenada Remota';

                title.innerText = city.toUpperCase();
                safeRender(content,
                    el('div', { className: 'flex justify-between border-b border-mole-border pb-1' },
                        el('span', { className: 'text-mole-text-dim' }, 'Condici\u00f3n:'),
                        el('span', { className: 'font-bold text-mole-cyan capitalize' }, desc)
                    ),
                    el('div', { className: 'flex justify-between border-b border-mole-border pb-1' },
                        el('span', { className: 'text-mole-text-dim' }, 'Temperatura:'),
                        el('span', { className: 'text-orange-400 font-mono' }, `${temp}\u00b0C`)
                    ),
                    el('div', { className: 'flex justify-between border-b border-mole-border pb-1' },
                        el('span', { className: 'text-mole-text-dim' }, 'Humedad:'),
                        el('span', { className: 'text-sky-400 font-mono' }, `${humidity}%`)
                    ),
                    el('div', { className: 'flex justify-between' },
                        el('span', { className: 'text-mole-text-dim' }, 'Coordenadas:'),
                        el('span', { className: 'text-mole-text font-mono text-[10px]' }, `${lat.toFixed(4)}, ${lng.toFixed(4)}`)
                    )
                );
            } else {
                throw new Error("Respuesta inv\u00e1lida");
            }
        } catch (error) {
            title.innerText = "ERROR DE CONEXI\u00d3N";
            safeRender(content,
                el('div', { className: 'text-mole-red' }, 'Fallo al contactar sat\u00e9lite meteorol\u00f3gico.')
            );
        }
    });
}

// 4. Dibujar los puntos de infecci n
async function loadMapPins() {
    if (!mapInstance || !layers.plagas) return;

    layers.plagas.clearLayers();

    let geoData = [];
    const currentUser = localStorage.getItem('moleia_current_user') || 'GLOBAL';
    const token = getAuthToken();

    try {
        if (!token) throw new Error("Acceso denegado: Se requiere Token.");
        geoData = await apiService.get(`map/hotspots/?user=${currentUser}`);
    } catch (error) {
        console.error("> [ ERROR CR\u00cdTICO ] Fallo al sincronizar radar t\u00e1ctico:", error);
        return;
    }

    if (geoData && geoData.length > 0) {
        const colorMap = { high: '#ef4444', critical: '#ef4444', medium: '#fbbf24', low: '#00e5ff', optimal: '#00e5ff' };
        
        geoData.forEach(point => {
            const severity = (point.severity || 'low').toLowerCase();
            const color = colorMap[severity] || '#9ca3af';

            const marker = L.circleMarker([point.lat, point.lng], {
                radius: 8, fillColor: color, color: '#fff', weight: 2, opacity: 1, fillOpacity: 0.8
            });

            // Reemplazo de bindPopup por inyecci n al Right Panel
            marker.on('click', (e) => {
                L.DomEvent.stopPropagation(e); // Evita que se dispare el evento del mapa vac o (clima)
                
                const panel = document.getElementById('map-info-panel');
                const title = document.getElementById('info-title');
                const content = document.getElementById('info-content');
                
                if(panel && title && content) {
                    panel.classList.remove('hidden');
                    title.innerText = (point.species || 'ESPECIE DESCONOCIDA').toUpperCase();
                    title.className = "text-sm font-bold text-mole-green tracking-wider truncate";
                    
                    safeRender(content,
                        el('div', { className: 'flex justify-between border-b border-mole-border pb-1' },
                            el('span', { className: 'text-mole-text-dim' }, 'Severidad:'),
                            el('span', { className: 'font-bold uppercase', style: { color } }, severity)
                        ),
                        el('div', { className: 'flex justify-between border-b border-mole-border pb-1' },
                            el('span', { className: 'text-mole-text-dim' }, 'Latitud:'),
                            el('span', { className: 'text-mole-text font-mono' }, point.lat.toFixed(4))
                        ),
                        el('div', { className: 'flex justify-between border-b border-mole-border pb-1' },
                            el('span', { className: 'text-mole-text-dim' }, 'Longitud:'),
                            el('span', { className: 'text-mole-text font-mono' }, point.lng.toFixed(4))
                        ),
                        el('button', {
                            className: 'w-full mt-2 py-1.5 text-xs font-bold text-mole-bg bg-mole-green hover:bg-mole-green/80 rounded transition-colors tracking-widest'
                        }, 'VER DETALLES')
                    );
                }
            });

            layers.plagas.addLayer(marker);
        });
    }
}