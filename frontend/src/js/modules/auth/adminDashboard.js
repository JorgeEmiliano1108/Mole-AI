// ==========================================================
// 4. FUNCIONES EXCLUSIVAS DEL ADMINISTRADOR Y AN LISIS [BACKEND READY]
// ==========================================================
// Chart.js is dynamically imported inside initAdminCharts to enable code splitting

let adminChart1, adminChart2, adminChart3;
let hChart, tChart; // Variables para las gr ficas de usuario normal

// ----------------------------------------------------
// 1. PANEL DE CONTROL GLOBAL (SOLO ADMIN)
// ----------------------------------------------------
async function initAdminCharts() {
    // Verificaci n de seguridad en el Frontend
    if (localStorage.getItem('moleia_user_role') !== 'admin') {
        console.error("> ACCESO DENEGADO: Nivel de autorizaci\u00f3n insuficiente.");
        return;
    }

    // Limpiamos gr ficas anteriores para evitar fugas de memoria (Canvas Overlap)
    if(adminChart1) adminChart1.destroy();
    if(adminChart2) adminChart2.destroy();
    if(adminChart3) adminChart3.destroy();

        // Dynamically import Chart.js only when needed (code splitting)
        let Chart;
        try {
            const mod = await import('chart.js/auto');
            Chart = mod.default || mod;
        } catch (e) {
            console.error('Failed to load Chart.js dynamically', e);
            return;
        }

    const chartStyle = { color: '#00e5ff', font: { family: 'Share Tech Mono' } };

    try {
        // ====================================================================
        //   CONEXI N AL BACKEND: Petici n segura de estad sticas globales
        // ====================================================================
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/admin/statistics`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${window.getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error("Error al obtener datos del servidor central");

        const data = await response.json();

        // Extracci n de datos con Fallback (Por si el backend manda datos vac os)
        const usuariosStats = data.usuarios || [1, 0, 0]; // [Activos, Inactivos, Suspendidos]
        const registrosStats = data.registros_semana || [0, 0, 0, 0, 0, 0, 0]; 
        const plantasStats = data.salud_plantas || [0, 0, 0, 0, 0]; 

        // GR FICA 1: USUARIOS (Doughnut)
        const ctx1 = document.getElementById('admin-chart-users').getContext('2d');
        adminChart1 = new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: ['Activos', 'Inactivos', 'Suspendidos'],
                datasets: [{
                    data: usuariosStats,
                    backgroundColor: ['#00e5ff', '#005577', '#ff4444'],
                    borderColor: '#000511',
                    borderWidth: 2
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: chartStyle } } }
        });

        // GR FICA 2: REGISTROS (Line)
        const ctx2 = document.getElementById('admin-chart-regs').getContext('2d');
        adminChart2 = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: ['LUN','MAR','MIE','JUE','VIE','SAB','DOM'],
                datasets: [{
                    label: 'Nuevos Operadores', 
                    data: registrosStats,
                    borderColor: '#00e5ff', backgroundColor: 'rgba(0, 229, 255, 0.2)', fill: true, tension: 0.3
                }]
            },
            options: { 
                responsive: true, maintainAspectRatio: false, 
                scales: { 
                    x: { ticks: chartStyle, grid: { color: 'rgba(0,229,255,0.1)' } },
                    y: { ticks: chartStyle, grid: { color: 'rgba(0,229,255,0.1)' } }
                },
                plugins: { legend: { display: false } }
            }
        });

        // GR FICA 3: SALUD DEL ECOSISTEMA (Radar)
        const ctx3 = document.getElementById('admin-chart-plants').getContext('2d');
        adminChart3 = new Chart(ctx3, {
            type: 'radar',
            data: {
                labels: ['Humedad', 'Temp.', 'Nutrientes', 'Radiaci\u00f3n UV', 'pH'],
                datasets: [{
                    label: 'Nivel Global',
                    data: plantasStats,
                    backgroundColor: 'rgba(0, 229, 255, 0.2)',
                    borderColor: '#00e5ff',
                    pointBackgroundColor: '#fff'
                }]
            },
            options: { 
                responsive: true, maintainAspectRatio: false,
                scales: { r: { grid: { color: 'rgba(0,229,255,0.3)' }, pointLabels: chartStyle, ticks: { display: false } } },
                plugins: { legend: { display: false } }
            }
        });

    } catch (error) {
        console.error("> Alerta de Supervisor: Fallo en telemetr\u00eda global.", error);
        // Aqu  podr as mostrar un mensaje de error visual en el dashboard de admin
    }
}

// Generaci n de Reporte TXT (Descarga con datos Reales del Backend)
async function downloadAdminReport() {
    try {
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/admin/report-text`, {
            headers: { 'Authorization': `Bearer ${window.getAuthToken()}` }
        });
        
        if (!response.ok) throw new Error("No se pudo generar el reporte.");
        
        const data = await response.json(); // Supongamos que el server nos manda un JSON con los totales
        
        const date = new Date().toLocaleString('en-GB');
        const fileContent = `
====================================================
      REPORTE DEL SISTEMA MOLE-IA - MODO ADMIN
====================================================
FECHA DE EXTRACCI\u00d3N: ${date}
SUPERVISOR A CARGO: ${localStorage.getItem('moleia_current_user').toUpperCase()}

--- ESTAD\u00cdSTICAS GLOBALES ---
TOTAL DE USUARIOS REGISTRADOS: ${data.total_usuarios || 'N/A'}
PLANTAS EN CUARENTENA: ${data.plantas_criticas || 'N/A'}
ESTADO DEL SERVIDOR: ONLINE

[FIN DEL REPORTE]
====================================================`;

        const blob = new Blob([fileContent], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `MOLE-IA_SUPERVISOR_${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("> Error al descargar reporte de admin:", error);
        alert("> ERROR: Fallo de conexi\u00f3n con la base de datos central.");
    }
}

// ----------------------------------------------------
// 2. UI Y GR FICAS DEL MODAL DE AN LISIS (USUARIO NORMAL)
// ----------------------------------------------------

async function renderLogList(plantName) {
    const logContainer = document.getElementById('log-list');
    if(!logContainer) return;
    
    logContainer.textContent = '';
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'text-[#00e5ff] animate-pulse';
    loadingDiv.textContent = '> Extrayendo bit\u00e1cora de la red...';
    logContainer.appendChild(loadingDiv);

    try {
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/plants/${plantName}/logs`, {
            headers: { 'Authorization': `Bearer ${window.getAuthToken()}` }
        });
        const logs = response.ok ? await response.json() : [];

        logContainer.textContent = ''; // clear loading
        if (logs.length === 0) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'text-white/50';
            emptyDiv.textContent = '> No hay eventos registrados recientemente.';
            logContainer.appendChild(emptyDiv);
            return;
        }

        const headerDiv = document.createElement('div');
        headerDiv.className = 'grid grid-cols-12 gap-4 text-[#00e5ff]/50 border-b border-[#00e5ff]/30 pb-2 mb-3 tracking-widest text-xs';
        
        ['HORA', 'EVENTO', 'DETALLE', 'ESTADO'].forEach((text, i) => {
            const col = document.createElement('div');
            col.className = i === 2 ? 'col-span-6 font-bold' : (i === 3 ? 'col-span-2 font-bold text-center' : 'col-span-2 font-bold');
            col.textContent = text;
            headerDiv.appendChild(col);
        });
        logContainer.appendChild(headerDiv);

        logs.forEach(log => {
            const row = document.createElement('div');
            row.className = 'grid grid-cols-12 gap-4 border-b border-[#00e5ff]/10 py-3 hover:bg-[#00e5ff]/5 transition-colors';

            const statusClass = log.status === '[WARN]' ? 'text-red-500 animate-pulse font-bold' : 
                              log.status === '[ACTIVE]' ? 'text-[#FBBF24]' : 'text-[#00e5ff]';

            const timeCol = document.createElement('div');
            timeCol.className = 'col-span-2 text-white font-bold opacity-80';
            timeCol.textContent = log.time;
            
            const eventCol = document.createElement('div');
            eventCol.className = 'col-span-2 text-white font-bold opacity-80';
            eventCol.textContent = log.event;

            const detailCol = document.createElement('div');
            detailCol.className = 'col-span-6 text-[#00e5ff] opacity-90';
            detailCol.textContent = log.detail;

            const statusCol = document.createElement('div');
            statusCol.className = `col-span-2 text-center ${statusClass}`;
            statusCol.textContent = log.status;

            row.appendChild(timeCol);
            row.appendChild(eventCol);
            row.appendChild(detailCol);
            row.appendChild(statusCol);
            logContainer.appendChild(row);
        });

    } catch (e) {
        logContainer.textContent = '';
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-red-500';
        errorDiv.textContent = '> Error al cargar la bit\u00e1cora.';
        logContainer.appendChild(errorDiv);
    }
}

async function openModal() {
    document.getElementById('main-dashboard').classList.add('hidden');
    document.getElementById('analysis-modal').classList.remove('hidden');
    document.getElementById('analysis-modal').classList.add('flex');
    
    // Saber qu  planta est  viendo el usuario actualmente
    const currentPlantName = document.getElementById('plant-tag').innerText.toLowerCase();

    const ctxH = document.getElementById('chart-hum').getContext('2d');
    const ctxT = document.getElementById('chart-temp').getContext('2d');
    
    const getChartOptions = (color, labelText) => ({
        responsive: true, maintainAspectRatio: false, 
        interaction: { mode: 'index', intersect: false }, 
        plugins: { 
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.85)', titleColor: color, bodyColor: '#ffffff', 
                titleFont: { family: 'Share Tech Mono', size: 14, weight: 'bold' },
                bodyFont: { family: 'Share Tech Mono', size: 14 },
                borderColor: color, borderWidth: 1.5, cornerRadius: 0, displayColors: false, padding: 10,
                callbacks: { label: (context) => `${labelText}: ${context.parsed.y}` }
            }
        },
        scales: {
            x: { grid: { color: 'rgba(0, 255, 170, 0.1)' }, ticks: { color: color, font: { family: 'Share Tech Mono' } } },
            y: { grid: { color: 'rgba(0, 255, 170, 0.1)' }, ticks: { color: color, font: { family: 'Share Tech Mono' } } }
        }
    });

    if (hChart) hChart.destroy(); if (tChart) tChart.destroy();

    try {
        // Pedimos los datos hist ricos (ej.  ltimas 7 horas) de ESA planta espec fica
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/plants/${currentPlantName}/history`, {
            headers: { 'Authorization': `Bearer ${window.getAuthToken()}` }
        });
        
        // Si el servidor falla, usamos un fallback visual por defecto (para que no se rompa la UI)
        const histData = response.ok ? await response.json() : {
            labels: ['00:00','04:00','08:00','12:00','16:00','20:00','24:00'],
            hum: [0,0,0,0,0,0,0],
            temp: [0,0,0,0,0,0,0]
        };
        
        hChart = new Chart(ctxH, { 
            type: 'line', 
            data: { 
                labels: histData.labels,
                datasets: [{ data: histData.hum, borderColor: '#00e5ff', backgroundColor: 'rgba(0, 255, 170, 0.1)', fill: true, tension: 0.4 }] 
            }, 
            options: getChartOptions('#00e5ff', 'Humedad') 
        });
        
        tChart = new Chart(ctxT, { 
            type: 'line', 
            data: { 
                labels: histData.labels,
                datasets: [{ data: histData.temp, borderColor: '#FBBF24', stepped: true }] 
            }, 
            options: getChartOptions('#FBBF24', 'Temperatura') 
        });

    } catch (e) {
        console.error("> Error graficando datos:", e);
    }

    // Renderizamos los eventos recientes de la planta
    renderLogList(currentPlantName);
}

export function closeModal() {
    document.getElementById('analysis-modal').classList.add('hidden');
    document.getElementById('analysis-modal').classList.remove('flex');
    document.getElementById('main-dashboard').classList.remove('hidden');
}

// Reloj global de la terminal
setInterval(() => { 
    const c = document.getElementById('clock');
    if(c) c.innerText = new Date().toLocaleTimeString('en-GB'); 
}, 1000);