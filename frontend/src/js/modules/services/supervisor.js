// ==========================================================
// 5. SISTEMAS DE SUPERVISOR (DIN MICO Y BACKEND READY)
// ==========================================================

/**
 * 1. SINCRONIZACI N DE INVENTARIO (OFFLINE-FRIENDLY)
 * Trae las plantas espec ficas del usuario desde el servidor.
 */
async function syncUserPlants() {
    try {
        const currentUser = localStorage.getItem('moleia_current_user'); 
        const token = window.getAuthToken();

        if (!currentUser || !token) return;

        const response = await fetch(`${window.AppConfig.API_BASE_URL}users/${currentUser}/plantas`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const userPlants = await response.json();
            // Guardamos el inventario real en la memoria local ( nica fuente de verdad)
            localStorage.setItem('moleia_plants', JSON.stringify(userPlants));
            console.log("> [ RED ] Banco de datos bot\u00e1nico sincronizado.");
        } else {
            throw new Error("Token expirado o acceso denegado.");
        }
    } catch (error) {
        console.warn("> [ MODO OFFLINE ] Usando matriz de datos local para el inventario.");
    }
}

/**
 * 2. OVERRIDE DIN MICO (ESTR S Y RESTAURACI N)
 * Conectado a la UI actual y con soporte para ca das de red.
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
        db[targetPlant].t = '48\u00b0C';
        console.warn(`> [ ALERTA ] Protocolo de sequ\u00eda activado en n\u00facleo: ${targetPlant.toUpperCase()}`);
    } 
    else if (type === 'restaurar') {
        // Restauraci n total: Pedimos datos frescos al servidor
        console.log("> [ SISTEMA ] Forzando restauraci\u00f3n de telemetr\u00eda...");
        await syncUserPlants();
        
        // Actualizamos la UI si el usuario est  viendo la misma planta
        if (typeof updatePlant === 'function') updatePlant(targetPlant);
        return;
    }

    // 1. Guardamos el da o en la memoria local inmediatamente
    localStorage.setItem('moleia_plants', JSON.stringify(db));
    
    // 2. Reflejamos el da o en la pantalla si esa planta est  activa
    if (typeof updatePlant === 'function') updatePlant(targetPlant);

    // 3. Informamos al servidor (Usando la cola offline del M dulo 2 si falla)
    try {
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/sistema/override`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.getAuthToken()}`
            },
            body: JSON.stringify({ plant: targetPlant, action: type, data: db[targetPlant] })
        });
        
        if (!response.ok) throw new Error("Servidor no respondi\u00f3 al Override.");
    } catch (e) { 
        console.warn("> [ RED CA\u00cdDA ] Override guardado en cach\u00e9. Se enviar\u00e1 al reconectar.");
        if (typeof queueOfflineAction === 'function') {
            queueOfflineAction('OVERRIDE', { plant: targetPlant, action: type, data: db[targetPlant] });
        }
    }
}

/**
 * 3. DIAGN STICO TOTAL (ESC NER TERMINAL)
 * Lee el inventario real y muestra el reporte con estilo Cyberpunk.
 */
async function runDiagnostic() {
    const term = document.getElementById('diagnostic-term');
    if (!term) return;
    
    term.textContent = '';
    const loadingSpan = document.createElement('span');
    loadingSpan.className = 'text-[#00e5ff] animate-pulse';
    loadingSpan.textContent = 'Iniciando enlace con sat\u00e9lite...';
    term.appendChild(loadingSpan);
    
    await syncUserPlants();
    const db = JSON.parse(localStorage.getItem('moleia_plants')) || {};
    const plantKeys = Object.keys(db);

    term.textContent = ''; // Limpiamos "cargando"

    let lines = [
        { text: "> INICIANDO PROTOCOLO DE DIAGN\u00d3STICO...", className: 'text-white font-bold' },
        { text: `> DETECTADOS ${plantKeys.length} ESPEC\u00cdMENES EN EL SECTOR...`, className: '' },
        { text: "----------------------------------------", className: 'text-[#00e5ff]/50' }
    ];

    if (plantKeys.length === 0) {
        lines.push({ text: "> ADVERTENCIA: SECTOR VAC\u00cdO.", className: 'text-red-500 font-bold' });
        lines.push({ text: "> REGISTRE NUEVAS ESPECIES PARA MONITOREO.", className: '' });
    } else {
        plantKeys.forEach(name => {
            const p = db[name];
            const hVal = parseInt(p.h.replace('%', '')) || 0; 
            
            lines.push({ text: `> N\u00daCLEO: ${name.toUpperCase()}`, className: 'text-white' });
            
            const statusLine = document.createElement('div');
            statusLine.appendChild(document.createTextNode("  ESTADO: "));
            const statusSpan = document.createElement('span');
            statusSpan.className = hVal < 20 ? 'text-red-500 font-bold animate-pulse' : 'text-[#00e5ff]';
            statusSpan.textContent = hVal < 20 ? '[ CR\u00cdTICO ]' : '[ \u00d3PTIMO ]';
            statusLine.appendChild(statusSpan);
            statusLine.appendChild(document.createTextNode(` | HUMEDAD: ${p.h} | TEMP: ${p.t}`));
            lines.push({ element: statusLine });

            const integrityLine = document.createElement('div');
            integrityLine.appendChild(document.createTextNode("  INTEGRIDAD: "));
            const intSpan = document.createElement('span');
            if (hVal < 20) {
                intSpan.className = 'text-red-500';
                intSpan.textContent = 'FALLO DE C\u00c1MARA';
            } else {
                intSpan.textContent = 'ESTABLE';
            }
            integrityLine.appendChild(intSpan);
            lines.push({ element: integrityLine });

            lines.push({ text: "  ...", className: '' });
        });
    }

    lines.push({ text: "----------------------------------------", className: 'text-[#00e5ff]/50' });
    lines.push({ text: "> ESCANEO FINALIZADO.", className: 'text-white font-bold' });

    let i = 0;
    const printInterval = setInterval(() => {
        if (i < lines.length) {
            const lineData = lines[i];
            const div = document.createElement('div');
            div.className = 'mb-1';
            if (lineData.element) {
                div.appendChild(lineData.element);
            } else {
                const span = document.createElement('span');
                if (lineData.className) span.className = lineData.className;
                span.textContent = lineData.text;
                div.appendChild(span);
            }
            term.appendChild(div);
            term.parentElement.scrollTop = term.parentElement.scrollHeight; 
            i++;
        } else {
            clearInterval(printInterval);
            const cursorDiv = document.createElement('div');
            cursorDiv.className = 'animate-pulse text-[#00e5ff] mt-2';
            cursorDiv.textContent = '_';
            term.appendChild(cursorDiv);
        }
    }, 250);
}