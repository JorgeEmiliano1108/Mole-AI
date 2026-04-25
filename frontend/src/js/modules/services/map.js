// ==========================================================
// 10. FLUJO DE GEOLOCALIZACIÓN (MAPA Y PERMISOS) [BACKEND ESTRICTO]
// ==========================================================
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export let mapInstance = null;
export let userLocation = null;
// Arreglo para guardar las referencias de los pines y borrarlos al actualizar
export let mapMarkers = []; 

// 1. Pedir permiso de ubicación EXACTA
export function requestLocation() {
    if ("geolocation" in navigator) {
        
        // GPS en modo "Francotirador" (Alta Precisión)
        const opcionesGPS = {
            enableHighAccuracy: true,
            timeout: 10000,          
            maximumAge: 0            
        };

        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = { lat: position.coords.latitude, lng: position.coords.longitude };
                console.log("> UBICACIÓN EXACTA CAPTURADA:", userLocation);

                // Si el mapa ya está abierto, lo centramos en ti con zoom 16
                if (mapInstance) {
                    mapInstance.setView([userLocation.lat, userLocation.lng], 16);
                }
            },
            (error) => {
                console.warn("> ACCESO A GPS DENEGADO O FALLIDO:", error.message);
            },
            opcionesGPS
        );
    } else {
        console.warn("> GEOLOCALIZACIÓN NO SOPORTADA POR EL NAVEGADOR.");
    }
}

// 2. Abrir el modal y renderizar el mapa base
export function openMapModal() {
    const modal = document.getElementById('map-modal');
    if(modal) modal.classList.remove('hidden');
    
    if (!mapInstance) {
        // Coordenadas iniciales (Centro de México), Zoom nivel 5
        mapInstance = L.map('map-container').setView([23.6345, -102.5528], 5);

        // Capa de mapa oscuro (Estilo Terminal/Cyberpunk)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20,
            keepBuffer: 4, 
            updateWhenZooming: false 
        }).addTo(mapInstance);
    } else {
        // Forzamos el redibujado del mapa al abrir el modal para evitar glitcheos grises
        setTimeout(() => mapInstance.invalidateSize(), 400);
        
        // Si tenemos la ubicación del usuario guardada, centramos el mapa ahí
        if (userLocation) {
            mapInstance.setView([userLocation.lat, userLocation.lng], 12);
        }
    }

    // 3. Cargar los pines de infección/distribución desde el Backend
    loadMapPins();
}

export function closeMapModal() {
    const modal = document.getElementById('map-modal');
    if(modal) modal.classList.add('hidden');
}

// 4. Dibujar los puntos de infección (BACKEND ESTRICTO)
async function loadMapPins() {
    if (!mapInstance) return;

    // 4.1 Limpiar pines anteriores para evitar fugas de memoria y duplicados
    mapMarkers.forEach(marker => mapInstance.removeLayer(marker));
    mapMarkers = []; 

    let geoData = [];
    const currentUser = localStorage.getItem('moleia_current_user') || 'GLOBAL';
    const token = window.getAuthToken();

    try {
        if (!token) throw new Error("Acceso denegado: Se requiere Token de Autenticación.");

        // ========================================================
        // 🚀 PETICIÓN AL SERVIDOR: Obtener coordenadas de los escaneos
        // ========================================================
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/map/distribution?user=${currentUser}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`El servidor rechazó la solicitud. Código: ${response.status}`);
        }
        
        geoData = await response.json();

    } catch (error) {
        console.error("> [ ERROR CRÍTICO ] Fallo al sincronizar radar táctico:", error);
        // NOTA: Al no haber datos de respaldo, 'geoData' se queda como un arreglo vacío.
        // El mapa simplemente se mostrará sin pines.
        return; 
    }

    // 4.2 Renderizar los pines reales del backend
    if (geoData && geoData.length > 0) {
        geoData.forEach(point => {
            // Asignación de color según el estado si el backend no manda un color explícito
            let pinColor = point.color;
            if (!pinColor) {
                const statusStr = (point.status || '').toLowerCase();
                if (statusStr.includes('óptimo') || statusStr.includes('sano')) pinColor = '#00ffaa'; // Verde
                else if (statusStr.includes('crítico') || statusStr.includes('infección')) pinColor = '#ef4444'; // Rojo
                else pinColor = '#f97316'; // Naranja/Atención por defecto
            }

            const customPin = L.divIcon({
                className: 'custom-pin',
                html: `<div style="background-color:${pinColor}; width:12px; height:12px; border-radius:50%; box-shadow: 0 0 15px ${pinColor}; border: 1px solid white;"></div>`,
                iconSize: [12, 12],
                iconAnchor: [6, 6]
            });

            // Agregamos el pin y su Popup
            const marker = L.marker([point.lat, point.lng], { icon: customPin })
                .addTo(mapInstance)
                .bindPopup(`
                    <div style="background:#001105; color:#00ffaa; border:1px solid #00ffaa; padding:8px; font-family:monospace; min-width: 150px; text-align: left;">
                        <strong style="color:white; display:block; border-bottom:1px solid rgba(0,255,170,0.3); padding-bottom:4px; margin-bottom:4px; text-transform:uppercase; font-size: 11px;">
                            ${point.species || 'ESPECIE DESCONOCIDA'}
                        </strong>
                        <span style="font-size: 10px;">Estado: <span style="color:${pinColor}; font-weight: bold;">${point.status || 'N/A'}</span></span>
                    </div>
                `);
            
            // Guardamos la referencia para poder borrarlo en la siguiente recarga
            mapMarkers.push(marker);
        });
    }
}