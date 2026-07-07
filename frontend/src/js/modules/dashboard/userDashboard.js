// ==========================================================
// 2. DASHBOARD DE USUARIO NORMAL (PLANTAS) - 100% FUNCIONAL
// ==========================================================

import { getAuthToken } from '../api/config.js';

// ==========================================================
// 2.2 MOTOR DE DATOS OFFLINE-FIRST (REEMPLAZA A LA SIMULACI N)//

/**
 * 1. OBTENER INVENTARIO REAL
 * Siempre lee de la memoria local, que es la  nica fuente de verdad para la UI.
 */
export function getUserPlants() {
    return JSON.parse(localStorage.getItem('moleia_plants')) || {};
}

/**
 * 2. COLA DE SINCRONIZACI N (OFFLINE QUEUE)
 * Si el usuario hace cambios sin internet, se guardan aqu .
 */
export function queueOfflineAction(actionType, payload) {
    let queue = JSON.parse(localStorage.getItem('moleia_sync_queue')) || [];
    queue.push({
        type: actionType,
        data: payload,
        timestamp: Date.now()
    });
    localStorage.setItem('moleia_sync_queue', JSON.stringify(queue));

    // Alerta visual en consola para el Operador
    console.warn(`> [ RED CA\u00cdDA ] Acci\u00f3n [${actionType}] guardada en memoria local. Se enviar\u00e1 al reconectar.`);
}

/**
 * 3. GUARDAR / MODIFICAR PLANTA (ESCRITURA H BRIDA)
 * Se usa cuando el usuario agrega o edita un cultivo.
 */
async function savePlantData(plantName, plantData) {
    // A. Reflejo Inmediato en Interfaz (Actualizamos LocalStorage)
    let currentPlants = getUserPlants();
    currentPlants[plantName] = plantData;
    localStorage.setItem('moleia_plants', JSON.stringify(currentPlants));

    // B. Intento de subida al Servidor
    if (navigator.onLine) {
        try {
            // Extraer valores num ricos de los datos simulados
            const valH = parseInt(String(plantData.h).replace(/[^0-9.-]/g, '')) || 0;
            const valT = parseInt(String(plantData.t).replace(/[^0-9.-]/g, '')) || 0;
            const valPH = parseFloat(plantData.ph) || 7.0;

            const sensorPayload = {
                plant_id: plantName, // El backend deber  resolver el nombre o recibir el UUID real
                recorded_at: new Date().toISOString(),
                soil_humidity: valH,
                air_temperature: valT,
                ph_level: valPH
            };

            const response = await fetch(`${window.AppConfig.API_BASE_URL}/sensor-data/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify(sensorPayload)
            });

            if (!response.ok) throw new Error("Fallo en el servidor.");
            console.log(`> [ ONLINE ] Especie ${plantName} respaldada en el servidor central.`);

        } catch (error) {
            // Si el servidor est  ca do (Error 500) aunque haya internet
            queueOfflineAction('SAVE_PLANT', { name: plantName, data: plantData });
        }
    } else {
        // Si el dispositivo no tiene internet
        queueOfflineAction('SAVE_PLANT', { name: plantName, data: plantData });
    }
}

/**
 * 4. ESCUCHADOR DE RECONEXI N (AUTO-SYNC)
 * El navegador dispara este evento m gicamente cuando vuelve el Wi-Fi o los Datos.
 */
window.addEventListener('online', async () => {
    console.log("> [ SISTEMA ] Enlace neuronal restablecido. Iniciando sincronizaci\u00f3n...");

    let queue = JSON.parse(localStorage.getItem('moleia_sync_queue')) || [];
    if (queue.length === 0) return console.log("> [ SISTEMA ] Memoria sincronizada. No hay datos pendientes.");

    // Procesamos cada acci n pendiente
    for (let task of queue) {
        if (task.type === 'SAVE_PLANT') {
            try {
                // Extraer num ricos
                const valH = parseInt(String(task.data.data.h).replace(/[^0-9.-]/g, '')) || 0;
                const valT = parseInt(String(task.data.data.t).replace(/[^0-9.-]/g, '')) || 0;
                const valPH = parseFloat(task.data.data.ph) || 7.0;

                await fetch(`${window.AppConfig.API_BASE_URL}/sensor-data/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getAuthToken()}`
                    },
                    body: JSON.stringify({
                        plant_id: task.data.name,
                        recorded_at: new Date(task.timestamp).toISOString(),
                        soil_humidity: valH,
                        air_temperature: valT,
                        ph_level: valPH
                    })
                });
            } catch (err) {
                console.error("> Fallo al sincronizar tarea:", err);
                return; // Rompemos el ciclo para no borrar la cola si el server sigue fallando
            }
        }
        // Aqu  podr as agregar m s tipos de tareas (DELETE_PLANT, UPDATE_SETTINGS, etc.)
    }

    // Si todo sali  bien, limpiamos la cola
    localStorage.removeItem('moleia_sync_queue');
    console.log("> [ SISTEMA ] Sincronizaci\u00f3n completada al 100%.");
});

/**
 * MOTOR DE ANIMACI N: Estilo terminal cyberpunk.
 */
export function animateValue(obj, start, end, duration, suffix = "") {
    if (!obj) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const currentVal = Math.floor(progress * (end - start) + start);
        obj.textContent = currentVal + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

/**
 * FUNCI N MAESTRA: Actualiza la telemetr a de la planta seleccionada.
 * Ahora prioriza los datos sincronizados desde el Backend.
 */
export function updatePlant(name) {
    // 1. Obtener datos de la memoria local (sincronizada previamente con el servidor)
    const localData = JSON.parse(localStorage.getItem('moleia_plants'));
    const data = (localData && localData[name]) ? localData[name] : plantDatabase[name];

    if (!data) {
        console.warn(`> Especie [${name}] no encontrada. Usando datos de emergencia.`);
        return;
    }

    const img = document.getElementById('main-img');
    const humEl = document.getElementById('txt-hum');
    const tempEl = document.getElementById('txt-temp');
    const phEl = document.getElementById('txt-ph');
    const uvEl = document.getElementById('txt-uv');
    const tagEl = document.getElementById('plant-tag');

    // 2. Efecto visual de transici n (Fade out)
    img.style.opacity = '0';

    setTimeout(() => {
        // 3. Renderizado de Informaci n Principal
        img.src = data.img;
        if (tagEl) tagEl.innerText = name.toUpperCase();

        // 4. Limpieza de datos (por si el servidor manda "65%" en vez de 65)
        const valH = parseInt(String(data.h).replace(/[^0-9]/g, '')) || 0;
        const valT = parseInt(String(data.t).replace(/[^0-9]/g, '')) || 0;

        // 5. Disparo de Animaciones
        animateValue(humEl, 0, valH, 800, '%');
        animateValue(tempEl, 0, valT, 800, '\u00b0C');

        if (phEl) phEl.innerText = data.ph || '--';
        if (uvEl) uvEl.innerText = data.uv || 'N/A';

        // 6. L GICA DE ALERTA CR TICA
        // Si la humedad baja del 20%, activamos modo visual de error
        if (valH < 20) {
            humEl.classList.add('text-red-500', 'animate-pulse');
            if (tagEl) tagEl.classList.add('text-red-500');
        } else {
            humEl.classList.remove('text-red-500', 'animate-pulse');
            if (tagEl) tagEl.classList.remove('text-red-500');
        }

        // 7. Reset de opacidad (Fade in)
        img.style.opacity = '1';
    }, 200);

    // Actualizar estado visual de los botones de navegaci n
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.innerText === name.toUpperCase());
    });
}

/**
 * INICIALIZADOR DE DASHBOARD
 * Llama a la primera planta disponible al entrar al sistema.
 */
export function initUserDashboard() {
    const localData = JSON.parse(localStorage.getItem('moleia_plants'));

    if (localData && Object.keys(localData).length > 0) {
        const firstPlant = Object.keys(localData)[0];
        updatePlant(firstPlant);

        // Si el M dulo 07 (Gesti n) est  presente, aseguramos que la UI est  en modo "Datos"
        if (typeof restoreDashboardUI === 'function') restoreDashboardUI();
    } else {
        // Si no hay plantas, activamos el estado de "Sin Se al" del M dulo 07
        if (typeof setEmptyDashboardState === 'function') {
            setEmptyDashboardState();
        }
    }
}

// Escuchamos si el sistema nos pide refrescar el dashboard
window.addEventListener('refreshDashboard', initUserDashboard);