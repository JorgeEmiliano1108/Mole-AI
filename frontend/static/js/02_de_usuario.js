// ==========================================================
// 2. DASHBOARD DE USUARIO NORMAL (PLANTAS) - 100% FUNCIONAL
// ==========================================================

// ==========================================================
// 2.2 MOTOR DE DATOS OFFLINE-FIRST (REEMPLAZA A LA SIMULACIÓN)//

/**
 * 1. OBTENER INVENTARIO REAL
 * Siempre lee de la memoria local, que es la única fuente de verdad para la UI.
 */
function getUserPlants() {
    return JSON.parse(localStorage.getItem('moleia_plants')) || {};
}

/**
 * 2. COLA DE SINCRONIZACIÓN (OFFLINE QUEUE)
 * Si el usuario hace cambios sin internet, se guardan aquí.
 */
function queueOfflineAction(actionType, payload) {
    let queue = JSON.parse(localStorage.getItem('moleia_sync_queue')) || [];
    queue.push({ 
        type: actionType, 
        data: payload, 
        timestamp: Date.now() 
    });
    localStorage.setItem('moleia_sync_queue', JSON.stringify(queue));
    
    // Alerta visual en consola para el Operador
    console.warn(`> [ RED CAÍDA ] Acción [${actionType}] guardada en memoria local. Se enviará al reconectar.`);
}

/**
 * 3. GUARDAR / MODIFICAR PLANTA (ESCRITURA HÍBRIDA)
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
            // Reemplaza con tu endpoint real
            const response = await fetch('http://localhost:3000/api/plantas/guardar', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${window.getAuthToken()}`
                },
                body: JSON.stringify({ name: plantName, data: plantData, user: localStorage.getItem('moleia_current_user') })
            });

            if (!response.ok) throw new Error("Fallo en el servidor.");
            console.log(`> [ ONLINE ] Especie ${plantName} respaldada en el servidor central.`);
            
        } catch (error) {
            // Si el servidor está caído (Error 500) aunque haya internet
            queueOfflineAction('SAVE_PLANT', { name: plantName, data: plantData });
        }
    } else {
        // Si el dispositivo no tiene internet
        queueOfflineAction('SAVE_PLANT', { name: plantName, data: plantData });
    }
}

/**
 * 4. ESCUCHADOR DE RECONEXIÓN (AUTO-SYNC)
 * El navegador dispara este evento mágicamente cuando vuelve el Wi-Fi o los Datos.
 */
window.addEventListener('online', async () => {
    console.log("> [ SISTEMA ] Enlace neuronal restablecido. Iniciando sincronización...");
    
    let queue = JSON.parse(localStorage.getItem('moleia_sync_queue')) || [];
    if (queue.length === 0) return console.log("> [ SISTEMA ] Memoria sincronizada. No hay datos pendientes.");

    // Procesamos cada acción pendiente
    for (let task of queue) {
        if (task.type === 'SAVE_PLANT') {
            try {
                await fetch('http://localhost:3000/api/plantas/guardar', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${window.getAuthToken()}`
                    },
                    body: JSON.stringify({ name: task.data.name, data: task.data.data, user: localStorage.getItem('moleia_current_user') })
                });
            } catch (err) {
                console.error("> Fallo al sincronizar tarea:", err);
                return; // Rompemos el ciclo para no borrar la cola si el server sigue fallando
            }
        }
        // Aquí podrías agregar más tipos de tareas (DELETE_PLANT, UPDATE_SETTINGS, etc.)
    }

    // Si todo salió bien, limpiamos la cola
    localStorage.removeItem('moleia_sync_queue');
    console.log("> [ SISTEMA ] Sincronización completada al 100%.");
});

/**
 * MOTOR DE ANIMACIÓN: Estilo terminal cyberpunk.
 */
function animateValue(obj, start, end, duration, suffix = "") {
    if (!obj) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const currentVal = Math.floor(progress * (end - start) + start);
        obj.innerHTML = currentVal + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

/**
 * FUNCIÓN MAESTRA: Actualiza la telemetría de la planta seleccionada.
 * Ahora prioriza los datos sincronizados desde el Backend.
 */
function updatePlant(name) {
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

    // 2. Efecto visual de transición (Fade out)
    img.style.opacity = '0';

    setTimeout(() => {
        // 3. Renderizado de Información Principal
        img.src = data.img; 
        if (tagEl) tagEl.innerText = name.toUpperCase();
        
        // 4. Limpieza de datos (por si el servidor manda "65%" en vez de 65)
        const valH = parseInt(String(data.h).replace(/[^0-9]/g, '')) || 0;
        const valT = parseInt(String(data.t).replace(/[^0-9]/g, '')) || 0;

        // 5. Disparo de Animaciones
        animateValue(humEl, 0, valH, 800, '%');
        animateValue(tempEl, 0, valT, 800, '°C');
        
        if (phEl) phEl.innerText = data.ph || '--';
        if (uvEl) uvEl.innerText = data.uv || 'N/A';

        // 6. LÓGICA DE ALERTA CRÍTICA
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
    
    // Actualizar estado visual de los botones de navegación
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.innerText === name.toUpperCase());
    });
}

/**
 * INICIALIZADOR DE DASHBOARD
 * Llama a la primera planta disponible al entrar al sistema.
 */
function initUserDashboard() {
    const localData = JSON.parse(localStorage.getItem('moleia_plants'));
    
    if (localData && Object.keys(localData).length > 0) {
        const firstPlant = Object.keys(localData)[0];
        updatePlant(firstPlant);
        
        // Si el Módulo 07 (Gestión) está presente, aseguramos que la UI esté en modo "Datos"
        if (typeof restoreDashboardUI === 'function') restoreDashboardUI();
    } else {
        // Si no hay plantas, activamos el estado de "Sin Señal" del Módulo 07
        if (typeof setEmptyDashboardState === 'function') {
            setEmptyDashboardState();
        }
    }
}

// Escuchamos si el sistema nos pide refrescar el dashboard
window.addEventListener('refreshDashboard', initUserDashboard);