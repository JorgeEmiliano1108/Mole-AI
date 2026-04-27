// ==========================================================
// 4. FUNCIONES EXCLUSIVAS DEL ADMINISTRADOR Y ANÁLISIS [BACKEND READY]
// ==========================================================

let adminChart1, adminChart2, adminChart3;
let hChart, tChart; // Variables para las gráficas de usuario normal

// ----------------------------------------------------
// 1. PANEL DE CONTROL GLOBAL (SOLO ADMIN)
// ----------------------------------------------------
async function initAdminCharts() {
    // Verificación de seguridad en el Frontend
    if (localStorage.getItem('moleia_user_role') !== 'admin') {
        console.error("> ACCESO DENEGADO: Nivel de autorización insuficiente.");
        return;
    }

    // Limpiamos gráficas anteriores para evitar fugas de memoria (Canvas Overlap)
    if(adminChart1) adminChart1.destroy();
    if(adminChart2) adminChart2.destroy();
    if(adminChart3) adminChart3.destroy();

    const chartStyle = { color: '#00e5ff', font: { family: 'Share Tech Mono' } };

    try {
        // ====================================================================
        // 🚀 CONEXIÓN AL BACKEND: Petición segura de estadísticas globales
        // ====================================================================
        const response = await fetch('http://localhost:3000/api/admin/estadisticas', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${window.getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error("Error al obtener datos del servidor central");

        const data = await response.json();

        // Extracción de datos con Fallback (Por si el backend manda datos vacíos)
        const usuariosStats = data.usuarios || [1, 0, 0]; // [Activos, Inactivos, Suspendidos]
        const registrosStats = data.registros_semana || [0, 0, 0, 0, 0, 0, 0]; 
        const plantasStats = data.salud_plantas || [0, 0, 0, 0, 0]; 

        // GRÁFICA 1: USUARIOS (Doughnut)
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

        // GRÁFICA 2: REGISTROS (Line)
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

        // GRÁFICA 3: SALUD DEL ECOSISTEMA (Radar)
        const ctx3 = document.getElementById('admin-chart-plants').getContext('2d');
        adminChart3 = new Chart(ctx3, {
            type: 'radar',
            data: {
                labels: ['Humedad', 'Temp.', 'Nutrientes', 'Radiación UV', 'pH'],
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
        console.error("> Alerta de Supervisor: Fallo en telemetría global.", error);
        // Aquí podrías mostrar un mensaje de error visual en el dashboard de admin
    }
}

// Generación de Reporte TXT (Descarga con datos Reales del Backend)
async function downloadAdminReport() {
    try {
        const response = await fetch('http://localhost:3000/api/admin/reporte-texto', {
            headers: { 'Authorization': `Bearer ${window.getAuthToken()}` }
        });
        
        if (!response.ok) throw new Error("No se pudo generar el reporte.");
        
        const data = await response.json(); // Supongamos que el server nos manda un JSON con los totales
        
        const date = new Date().toLocaleString('en-GB');
        const fileContent = `
====================================================
      REPORTE DEL SISTEMA MOLE-IA - MODO ADMIN
====================================================
FECHA DE EXTRACCIÓN: ${date}
SUPERVISOR A CARGO: ${localStorage.getItem('moleia_current_user').toUpperCase()}

--- ESTADÍSTICAS GLOBALES ---
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
        alert("> ERROR: Fallo de conexión con la base de datos central.");
    }
}

// ----------------------------------------------------
// 2. UI Y GRÁFICAS DEL MODAL DE ANÁLISIS (USUARIO NORMAL)
// ----------------------------------------------------

async function renderLogList(plantName) {
    const logContainer = document.getElementById('log-list');
    if(!logContainer) return;
    
    logContainer.innerHTML = '<div class="text-[#00e5ff] animate-pulse">> Extrayendo bitácora de la red...</div>';

    try {
        // Obtenemos los logs reales de esa planta específica
        const response = await fetch(`http://localhost:3000/api/plantas/${plantName}/logs`, {
            headers: { 'Authorization': `Bearer ${window.getAuthToken()}` }
        });
        const logs = response.ok ? await response.json() : [];

        if (logs.length === 0) {
            logContainer.innerHTML = '<div class="text-white/50">> No hay eventos registrados recientemente.</div>';
            return;
        }

        let logHTML = `
            <div class="grid grid-cols-12 gap-4 text-[#00e5ff]/50 border-b border-[#00e5ff]/30 pb-2 mb-3 tracking-widest text-xs">
                <div class="col-span-2 font-bold">HORA</div>
                <div class="col-span-2 font-bold">EVENTO</div>
                <div class="col-span-6 font-bold">DETALLE</div>
                <div class="col-span-2 font-bold text-center">ESTADO</div>
            </div>
        `;

        logHTML += logs.map(log => {
            let statusClass = log.status === '[WARN]' ? 'text-red-500 animate-pulse font-bold' : 
                              log.status === '[ACTIVE]' ? 'text-[#FBBF24]' : 'text-[#00e5ff]';

            return `
                <div class="grid grid-cols-12 gap-4 border-b border-[#00e5ff]/10 py-3 hover:bg-[#00e5ff]/5 transition-colors">
                    <div class="col-span-2 text-white font-bold opacity-80">${log.time}</div>
                    <div class="col-span-2 text-white font-bold opacity-80">${log.event}</div>
                    <div class="col-span-6 text-[#00e5ff] opacity-90">${log.detail}</div>
                    <div class="col-span-2 text-center ${statusClass}">${log.status}</div>
                </div>
            `;
        }).join('');

        logContainer.innerHTML = logHTML;

    } catch (e) {
        logContainer.innerHTML = '<div class="text-red-500">> Error al cargar la bitácora.</div>';
    }
}

async function openModal() {
    document.getElementById('main-dashboard').classList.add('hidden');
    document.getElementById('analysis-modal').classList.remove('hidden');
    document.getElementById('analysis-modal').classList.add('flex');
    
    // Saber qué planta está viendo el usuario actualmente
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
        // Pedimos los datos históricos (ej. últimas 7 horas) de ESA planta específica
        const response = await fetch(`http://localhost:3000/api/plantas/${currentPlantName}/historial`, {
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

function closeModal() {
    document.getElementById('analysis-modal').classList.add('hidden');
    document.getElementById('analysis-modal').classList.remove('flex');
    document.getElementById('main-dashboard').classList.remove('hidden');
}

// Reloj global de la terminal
setInterval(() => { 
    const c = document.getElementById('clock');
    if(c) c.innerText = new Date().toLocaleTimeString('en-GB'); 
}, 1000);