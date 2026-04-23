// ==========================================================
// 6. SISTEMA DE REPORTES DUALES (ADMIN) [BACKEND READY]
// ==========================================================

// --- LÓGICA DEL MODAL DE CONTACTO (OPERADORES) ---
export function openContactModal() {
    const modal = document.getElementById('contact-modal');
    if (!modal) return;
    modal.classList.remove('hidden');
    
    const currentUser = localStorage.getItem('moleia_current_user');
    document.getElementById('contact-user').value = currentUser ? currentUser.toUpperCase() : "OPERADOR_DESCONOCIDO";
}

export function closeContactModal() {
    document.getElementById('contact-modal').classList.add('hidden');
    document.getElementById('contact-status').classList.add('hidden');
    document.getElementById('contact-msg').value = ''; 
}

// --- ENVÍO DE REPORTE MANUAL (BANDEJA 1) ---
export function sendReport() {
    const btnStatus = document.getElementById('contact-status');
    const msgInput = document.getElementById('contact-msg');
    const msg = msgInput.value;
    
    if(msg.trim() === '') {
        btnStatus.innerText = "ERROR: LA BITÁCORA ESTÁ VACÍA.";
        btnStatus.className = "text-center mt-4 text-xs font-bold text-red-500 animate-pulse tracking-widest";
        btnStatus.classList.remove('hidden');
        return;
    }

    btnStatus.innerText = "> ENCRIPTANDO Y ENVIANDO DATOS...";
    btnStatus.className = "text-center mt-4 text-xs font-bold text-[#f97316] animate-pulse tracking-widest";
    btnStatus.classList.remove('hidden');

    setTimeout(async () => {
        const reportData = { 
            user: document.getElementById('contact-user').value, 
            type: document.getElementById('contact-type').value, 
            message: msg,
            time: new Date().toLocaleString('en-GB')
        };

        try {
            const token = window.getAuthToken();
            // Endpoint para reportes de usuarios
            const response = await fetch(`${window.AppConfig.API_BASE_URL}/reports/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(reportData)
            });

            if (response.ok) {
                btnStatus.innerText = "TRANSMISIÓN EXITOSA. CENTRAL NOTIFICADA.";
                btnStatus.className = "text-center mt-4 text-xs font-bold text-[#00ffaa] tracking-widest";
                msgInput.value = '';
                setTimeout(() => { closeContactModal(); }, 2000);
            } else throw new Error("Central rechazó la transmisión.");
        } catch (error) {
            console.warn("> [ MODO OFFLINE ] Guardando reporte de usuario en memoria local.");
            let localReports = JSON.parse(localStorage.getItem('moleia_user_reports')) || [];
            localReports.push(reportData);
            localStorage.setItem('moleia_user_reports', JSON.stringify(localReports));

            btnStatus.innerText = "RED CAÍDA: REPORTE GUARDADO EN MEMORIA LOCAL.";
            btnStatus.className = "text-center mt-4 text-xs font-bold text-[#eab308] tracking-widest";
            msgInput.value = '';
            setTimeout(() => { closeContactModal(); }, 2500);
        }
    }, 1500);
}

// --- REGISTRO AUTOMÁTICO DE ANOMALÍAS EN PLANTAS (BANDEJA 2) ---
// (Puedes llamar esta función desde el Módulo 5 cuando una planta entra en estado Crítico)
async function logPlantIssue(plantName, issueDetails) {
    const currentUser = localStorage.getItem('moleia_current_user') || "SISTEMA";
    const reportData = {
        user: currentUser.toUpperCase(),
        plant: plantName.toUpperCase(),
        issue: issueDetails,
        time: new Date().toLocaleString('en-GB')
    };

    try {
        const token = window.getAuthToken();
        // Endpoint para reportes de plantas/sistemas
        await fetch(`${window.AppConfig.API_BASE_URL}/reports/plants`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(reportData)
        });
    } catch (e) {
        let localPlantReports = JSON.parse(localStorage.getItem('moleia_plant_reports')) || [];
        localPlantReports.push(reportData);
        localStorage.setItem('moleia_plant_reports', JSON.stringify(localPlantReports));
    }
}

// --- RENDERIZADO DUAL PARA EL PANEL DE ADMIN ---
async function renderAdminReports() {
    const userContainer = document.getElementById('user-reports-list');
    const plantContainer = document.getElementById('plant-reports-list');
    
    if(userContainer) {
        userContainer.textContent = '';
        userContainer.appendChild(createNode('div', 'text-center opacity-50 text-xs py-8 animate-pulse', '> DESCARGANDO DATOS DE OPERADORES...'));
    }
    if(plantContainer) {
        plantContainer.textContent = '';
        plantContainer.appendChild(createNode('div', 'text-center opacity-50 text-xs py-8 animate-pulse', '> DESCARGANDO BITÁCORA BOTÁNICA...'));
    }

    const token = window.getAuthToken();
    
    // 1. CARGAR REPORTES DE USUARIOS
    let userReports = [];
    try {
        const resU = await fetch(`${window.AppConfig.API_BASE_URL}/reports/users`, { headers: { 'Authorization': `Bearer ${token}` } });
        if(resU.ok) userReports = await resU.json();
    } catch (e) {
        userReports = JSON.parse(localStorage.getItem('moleia_user_reports')) || [];
    }
    window.systemUserReports = userReports; // Guardar en global para exportar

    // 2. CARGAR REPORTES DE PLANTAS
    let plantReports = [];
    try {
        const resP = await fetch(`${window.AppConfig.API_BASE_URL}/reports/plants`, { headers: { 'Authorization': `Bearer ${token}` } });
        if(resP.ok) plantReports = await resP.json();
    } catch (e) {
        plantReports = JSON.parse(localStorage.getItem('moleia_plant_reports')) || [];
    }
    window.systemPlantReports = plantReports; // Guardar en global para exportar

    // 3. PINTAR BANDEJA DE USUARIOS
    if(userContainer) {
        userContainer.textContent = '';
        if(userReports.length === 0) {
            userContainer.appendChild(createNode('div', 'text-center opacity-50 text-xs py-8', '> NO HAY REPORTES DE OPERADORES...'));
        } else {
            [...userReports].reverse().forEach(rep => {
                const row = createNode('div', 'grid grid-cols-12 gap-4 text-xs border-b border-[#00e5ff]/10 py-3 px-2 hover:bg-[#00e5ff]/10 transition-colors');
                row.appendChild(createNode('div', 'col-span-2 text-[#00e5ff]/70 font-bold', rep.time));
                row.appendChild(createNode('div', 'col-span-3 text-white', rep.user));
                row.appendChild(createNode('div', 'col-span-3 text-[#f97316] uppercase font-bold', (rep.type || '').replace('_', ' ')));
                row.appendChild(createNode('div', 'col-span-4 opacity-80 break-words', rep.message));
                userContainer.appendChild(row);
            });
        }
    }

    // 4. PINTAR BANDEJA DE PLANTAS
    if(plantContainer) {
        plantContainer.textContent = '';
        if(plantReports.length === 0) {
            plantContainer.appendChild(createNode('div', 'text-center opacity-50 text-xs py-8', '> NO HAY ANOMALÍAS BOTÁNICAS...'));
        } else {
            [...plantReports].reverse().forEach(rep => {
                const row = createNode('div', 'grid grid-cols-12 gap-4 text-xs border-b border-red-500/10 py-3 px-2 hover:bg-red-500/10 transition-colors');
                row.appendChild(createNode('div', 'col-span-2 text-red-400/70 font-bold', rep.time));
                row.appendChild(createNode('div', 'col-span-3 text-white', rep.user));
                row.appendChild(createNode('div', 'col-span-3 text-[#00ffaa] font-bold', `NÚCLEO: ${rep.plant}`));
                row.appendChild(createNode('div', 'col-span-4 opacity-80 text-red-300 break-words', rep.issue));
                plantContainer.appendChild(row);
            });
        }
    }
}

// --- EXPORTACIÓN INTELIGENTE (RECIBE EL TIPO DE REPORTE) ---
export function generateMasterReport(type) {
    let targetData = [];
    let title = "";

    if (type === 'usuarios') {
        targetData = window.systemUserReports || [];
        title = "REPORTE MAESTRO DE OPERADORES";
    } else if (type === 'plantas') {
        targetData = window.systemPlantReports || [];
        title = "BITÁCORA DE ANOMALÍAS BOTÁNICAS";
    }

    if(targetData.length === 0) {
        alert("SISTEMA OVERRIDE: No hay registros para compilar en esta bandeja.");
        return;
    }
    
    let reportText = "==========================================\n";
    reportText += `   MOLE-IA | ${title} \n`;
    reportText += "==========================================\n\n";
    reportText += `FECHA DE EXTRACCIÓN: ${new Date().toLocaleDateString('en-GB')} - ${new Date().toLocaleTimeString('en-GB')}\n\n`;
    
    targetData.forEach(r => {
        if(type === 'usuarios') {
            reportText += `[${r.time}] | OPERADOR: ${r.user} | CLASIFICACIÓN: ${r.type.toUpperCase().replace('_', ' ')}\n`;
            reportText += `>> REPORTE: ${r.message}\n`;
        } else {
            reportText += `[${r.time}] | OPERADOR: ${r.user} | ESPECÍMEN: ${r.plant}\n`;
            reportText += `>> FALLO DETECTADO: ${r.issue}\n`;
        }
        reportText += `------------------------------------------\n`;
    });
    
    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MOLE_IA_${type.toUpperCase()}_${Date.now()}.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
}