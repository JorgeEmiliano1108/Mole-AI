// ==========================================================
// 5. SISTEMAS DE SUPERVISOR (DINÁMICO Y BACKEND READY)
// ==========================================================

/**
 * 1. SINCRONIZACIÓN DE INVENTARIO (OFFLINE-FRIENDLY)
 * Trae las plantas específicas del usuario desde el servidor.
 */
async function syncUserPlants() {
    try {
        const currentUser = localStorage.getItem('moleia_current_user'); 
        const token = localStorage.getItem('moleia_token');

        if (!currentUser || !token) return;

        const response = await fetch(`http://localhost:3000/api/usuarios/${currentUser}/plantas`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const userPlants = await response.json();
            // Guardamos el inventario real en la memoria local (Única fuente de verdad)
            localStorage.setItem('moleia_plants', JSON.stringify(userPlants));
            console.log("> [ RED ] Banco de datos botánico sincronizado.");
        } else {
            throw new Error("Token expirado o acceso denegado.");
        }
    } catch (error) {
        console.warn("> [ MODO OFFLINE ] Usando matriz de datos local para el inventario.");
    }
}

/**
 * 2. OVERRIDE DINÁMICO (ESTRÉS Y RESTAURACIÓN)
 * Conectado a la UI actual y con soporte para caídas de red.
 */
async function triggerOverride(type, plantName = null) {
    const db = JSON.parse(localStorage.getItem('moleia_plants')) || {};
    
    // Si no se especifica, leemos la planta que el usuario tiene abierta en pantalla
    let targetPlant = plantName;
    if (!targetPlant) {
        const tagElement = document.getElementById('plant-tag');
        targetPlant = tagElement ? tagElement.innerText.toLowerCase() : Object.keys(db)[0];
    }
    
    if (!targetPlant || !db[targetPlant]) {
        console.error("> ERROR: Especie no localizada en los registros del operador.");
        return;
    }

    if (type === 'sequia') {
        db[targetPlant].h = '5%';
        db[targetPlant].t = '48°C';
        console.warn(`> [ ALERTA ] Protocolo de sequía activado en núcleo: ${targetPlant.toUpperCase()}`);
    } 
    else if (type === 'restaurar') {
        // Restauración total: Pedimos datos frescos al servidor
        console.log("> [ SISTEMA ] Forzando restauración de telemetría...");
        await syncUserPlants();
        
        // Actualizamos la UI si el usuario está viendo la misma planta
        if (typeof updatePlant === 'function') updatePlant(targetPlant);
        return;
    }

    // 1. Guardamos el daño en la memoria local inmediatamente
    localStorage.setItem('moleia_plants', JSON.stringify(db));
    
    // 2. Reflejamos el daño en la pantalla si esa planta está activa
    if (typeof updatePlant === 'function') updatePlant(targetPlant);

    // 3. Informamos al servidor (Usando la cola offline del Módulo 2 si falla)
    try {
        const response = await fetch('http://localhost:3000/api/sistema/override', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('moleia_token')}`
            },
            body: JSON.stringify({ plant: targetPlant, action: type, data: db[targetPlant] })
        });
        
        if (!response.ok) throw new Error("Servidor no respondió al Override.");
    } catch (e) { 
        console.warn("> [ RED CAÍDA ] Override guardado en caché. Se enviará al reconectar.");
        if (typeof queueOfflineAction === 'function') {
            queueOfflineAction('OVERRIDE', { plant: targetPlant, action: type, data: db[targetPlant] });
        }
    }
}

/**
 * 3. DIAGNÓSTICO TOTAL (ESCÁNER TERMINAL)
 * Lee el inventario real y muestra el reporte con estilo Cyberpunk.
 */
async function runDiagnostic() {
    const term = document.getElementById('diagnostic-term');
    if (!term) return;
    
    // Preparamos la terminal
    term.innerHTML = '<span class="text-[#00ffaa] animate-pulse">Iniciando enlace con satélite...</span>';
    
    // 1. Refrescamos datos antes del scan
    await syncUserPlants();
    const db = JSON.parse(localStorage.getItem('moleia_plants')) || {};
    const plantKeys = Object.keys(db);

    term.innerHTML = ''; // Limpiamos "cargando"

    let lines = [
        "<span class='text-white font-bold'>> INICIANDO PROTOCOLO DE DIAGNÓSTICO...</span>",
        `> DETECTADOS ${plantKeys.length} ESPECÍMENES EN EL SECTOR...`,
        "<span class='text-[#00ffaa]/50'>----------------------------------------</span>"
    ];

    if (plantKeys.length === 0) {
        lines.push("<span class='text-red-500 font-bold'>> ADVERTENCIA: SECTOR VACÍO.</span>");
        lines.push("> REGISTRE NUEVAS ESPECIES PARA MONITOREO.");
    } else {
        // 2. Mapeo dinámico del inventario del usuario
        plantKeys.forEach(name => {
            const p = db[name];
            // Extraemos solo el número de '65%'
            const hVal = parseInt(p.h.replace('%', '')) || 0; 
            const statusLabel = hVal < 20 ? "<span class='text-red-500 font-bold animate-pulse'>[ CRÍTICO ]</span>" : "<span class='text-[#00ffaa]'>[ ÓPTIMO ]</span>";
            
            lines.push(`<span class='text-white'>> NÚCLEO: ${name.toUpperCase()}</span>`);
            lines.push(`  ESTADO: ${statusLabel} | HUMEDAD: ${p.h} | TEMP: ${p.t}`);
            lines.push(`  INTEGRIDAD: ${hVal < 20 ? "<span class='text-red-500'>FALLO DE CÁMARA</span>" : "ESTABLE"}`);
            lines.push("  ...");
        });
    }

    lines.push("<span class='text-[#00ffaa]/50'>----------------------------------------</span>");
    lines.push("<span class='text-white font-bold'>> ESCANEO FINALIZADO.</span>");

    // 3. Efecto de máquina de escribir en la terminal
    let i = 0;
    const printInterval = setInterval(() => {
        if (i < lines.length) {
            term.innerHTML += `<div class="mb-1">${lines[i]}</div>`;
            term.parentElement.scrollTop = term.parentElement.scrollHeight; 
            i++;
        } else {
            clearInterval(printInterval);
            // Agregamos el cursor parpadeante al final
            term.innerHTML += `<div class="animate-pulse text-[#00ffaa] mt-2">_</div>`;
        }
    }, 250); // Velocidad ajustada para mayor dramatismo
}