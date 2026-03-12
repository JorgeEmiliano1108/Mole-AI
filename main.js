// ==========================================================
// 1. SISTEMA DE LOGIN Y REGISTRO (MULTINIVEL)
// ==========================================================

const introData = {
    'objetivo': "> OBJETIVO:\n\nEstablecer un sistema de monitoreo biométrico continuo para la preservación de especies vegetales.",
    'vision': "> VISIÓN:\n\nCrear el banco de datos botánico más resistente del yermo.",
    'flora': "> FLORA MEXICANA:\n\nCatálogo de especímenes recuperados en cuarentena hidro-botánica.",
    'acerca': "> ACERCA DE LA WEB:\n\nTerminal MOLE-IA versión 1.0.5\nSistema Seguro, Encriptado y Multi-Rol."
};

let typeInterval;

function initUsers() {
    if (!localStorage.getItem('moleia_users')) {
        // Creamos el admin por defecto
        const defaultUsers = { 'admin': 'admin' };
        localStorage.setItem('moleia_users', JSON.stringify(defaultUsers));
    }
}
initUsers();

function typeContent(section) {
    const output = document.getElementById('typewriter-output');
    const text = introData[section];
    output.innerHTML = ''; 
    clearInterval(typeInterval); 
    let currentText = "", i = 0;
    
    typeInterval = setInterval(() => {
        currentText += text.charAt(i);
        output.innerHTML = currentText + '<span class="animate-pulse">_</span>';
        i++;
        if (i === text.length) clearInterval(typeInterval);
    }, 20);
}

function startSystem() {
    document.getElementById('intro-screen').classList.add('hidden');
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('login-error').classList.add('hidden');
    clearInterval(typeInterval);
}

function showRegisterScreen() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('register-screen').classList.remove('hidden');
    document.getElementById('reg-user-input').value = '';
    document.getElementById('reg-pass-input').value = '';
    document.getElementById('reg-error').classList.add('hidden');
    document.getElementById('reg-success').classList.add('hidden');
}

function backToLogin() {
    document.getElementById('register-screen').classList.add('hidden');
    document.getElementById('login-screen').classList.remove('hidden');
}

function submitRegistration() {
    const user = document.getElementById('reg-user-input').value.trim();
    const pass = document.getElementById('reg-pass-input').value.trim();
    const errorMsg = document.getElementById('reg-error');
    const successMsg = document.getElementById('reg-success');

    errorMsg.classList.add('hidden');
    successMsg.classList.add('hidden');

    if (user.length < 3 || pass.length < 3) {
        errorMsg.innerText = "ERROR: MÍNIMO 3 CARACTERES.";
        errorMsg.classList.remove('hidden');
        return;
    }

    if (user.toLowerCase() === 'admin') {
        errorMsg.innerText = "ERROR: NOMBRE RESERVADO POR EL SISTEMA.";
        errorMsg.classList.remove('hidden');
        return;
    }

    const users = JSON.parse(localStorage.getItem('moleia_users'));
    if (users[user]) {
        errorMsg.innerText = "ERROR: EL USUARIO YA EXISTE.";
        errorMsg.classList.remove('hidden');
    } else {
        users[user] = pass;
        localStorage.setItem('moleia_users', JSON.stringify(users));
        successMsg.innerText = `USUARIO "${user.toUpperCase()}" CREADO.`;
        successMsg.classList.remove('hidden');
    }
}

// --- NUEVA VERSIÓN DE ATTEMPT LOGIN CON ANIMACIONES PRIME ---
function attemptLogin() {
    const user = document.getElementById('user-input').value.trim();
    const pass = document.getElementById('pass-input').value.trim();
    const errorMsg = document.getElementById('login-error');

    errorMsg.classList.add('hidden');
    const users = JSON.parse(localStorage.getItem('moleia_users'));

    if (users[user] && users[user] === pass) {
        
        const loginScreen = document.getElementById('login-screen');

        // =========================================================
        // ANIMACIÓN PARA EL ADMIN (ESTÁTICA Y PODER)
        // =========================================================
        if (user.toLowerCase() === 'admin') {
            
            // 1. Inyectamos keyframes de estática si no existen
            if (!document.getElementById('admin-glitch-style')) {
                const style = document.createElement('style');
                style.id = 'admin-glitch-style';
                style.innerHTML = `
                    @keyframes pure-static {
                        0% { background-position: 0% 0%; filter: invert(0%) sepia(100%) hue-rotate(180deg) saturate(500%); }
                        25% { background-position: 50% 50%; filter: invert(100%); }
                        50% { background-position: -20% 30%; filter: invert(0%); }
                        75% { background-position: 80% -10%; filter: invert(100%); }
                        100% { background-position: 100% 100%; filter: invert(0%); }
                    }
                `;
                document.head.appendChild(style);
            }

            // 2. Creamos el overlay negro absoluto
            const overlay = document.createElement('div');
            overlay.className = 'fixed inset-0 z-[9999] flex items-center justify-center bg-black';
            document.body.appendChild(overlay);

            // 3. Creamos la capa de ruido (glitch visual)
            const noise = document.createElement('div');
            noise.className = 'absolute inset-0';
            noise.style.backgroundImage = 'repeating-radial-gradient(circle at 17% 32%, #ffffff, #000000 0.001px)';
            noise.style.animation = 'pure-static 0.1s infinite';
            noise.style.opacity = '0.85';
            overlay.appendChild(noise);

            // Ocultamos el login por debajo para que no estorbe
            loginScreen.classList.add('hidden');

            // 4. Secuencia de tiempos
            setTimeout(() => {
                // A los 1.5s quitamos la estática y dejamos la pantalla negra
                noise.remove(); 
                
                // Agregamos el mensaje del supervisor
                const msg = document.createElement('h1');
                msg.innerText = "> BIENVENIDO SUPERVISOR";
                msg.className = "text-[#00e5ff] font-bold text-3xl md:text-5xl tracking-[0.3em] uppercase drop-shadow-[0_0_15px_#00e5ff] animate-pulse text-center px-4";
                msg.style.fontFamily = "'Share Tech Mono', monospace";
                overlay.appendChild(msg);

                setTimeout(() => {
                    // Después de leer el mensaje, se desvanece
                    overlay.style.transition = 'opacity 0.8s ease';
                    overlay.style.opacity = '0';
                    
                    // Mostramos el dashboard azul
                    const adminDash = document.getElementById('admin-dashboard');
                    adminDash.classList.remove('hidden');
                    adminDash.classList.add('flex');
                    initAdminCharts(); 
                    renderAdminReports();

                    // Destruimos el overlay para liberar memoria
                    setTimeout(() => overlay.remove(), 800); 
                }, 2500); // 2.5 segundos mostrando el mensaje

            }, 1500); // 1.5 segundos de estática salvaje
        } 
        
        // =========================================================
        // ANIMACIÓN PARA EL USUARIO (APAGADO Y ENCENDIDO DE TV VIEJA)
        // =========================================================
        else {
            // 1. Efecto "Apagar TV"
            loginScreen.style.transformOrigin = 'center';
            loginScreen.style.transition = 'transform 0.2s ease-in, filter 0.2s ease-in';
            loginScreen.style.filter = 'brightness(8) contrast(2)';
            loginScreen.style.transform = 'scale(1, 0.005)'; 
            
            setTimeout(() => {
                // Se chupa al centro y desaparece
                loginScreen.style.transform = 'scale(0, 0.005)'; 
                
                setTimeout(() => {
                    loginScreen.classList.add('hidden');
                    
                    // Limpiamos estilos para que no haya bugs al cerrar sesión
                    loginScreen.style.transform = '';
                    loginScreen.style.filter = '';
                    loginScreen.style.transition = '';
                    
                    // 2. Tiempo de Oscuridad (Pantalla muerta)
                    setTimeout(() => {
                        
                        // 3. Efecto "Encender TV"
                        const dashboard = document.getElementById('main-dashboard');
                        dashboard.classList.remove('hidden');
                        dashboard.classList.add('flex');
                        
                        dashboard.style.transformOrigin = 'center';
                        dashboard.style.transform = 'scale(0, 0.005)';
                        dashboard.style.filter = 'brightness(8) contrast(2)';
                        
                        void dashboard.offsetWidth; // Forzamos reflow

                        dashboard.style.transition = 'transform 0.2s ease-out, filter 0.2s ease-out';
                        dashboard.style.transform = 'scale(1, 0.005)'; 
                        
                        setTimeout(() => {
                            dashboard.style.transform = 'scale(1, 1)'; 
                            dashboard.style.filter = 'brightness(1) contrast(1)'; 
                            
                            setTimeout(() => {
                                dashboard.style.transform = '';
                                dashboard.style.filter = '';
                                dashboard.style.transition = '';
                                dashboard.style.transformOrigin = '';
                                loadChatHistory();
                            }, 250);
                        }, 200);

                    }, 2500); // Tiempo apagado

                }, 200);
            }, 200);
        }
        
        // Limpiamos los campos del formulario
        document.getElementById('user-input').value = '';
        document.getElementById('pass-input').value = '';

    } else {
        errorMsg.innerText = "ACCESO DENEGADO. CREDENCIALES INVÁLIDAS.";
        errorMsg.classList.remove('hidden');
    }
}

// PEGA ESTO (La versión con el efecto TV):
function logout() {
    const mainDash = document.getElementById('main-dashboard');
    const adminDash = document.getElementById('admin-dashboard');
    const activeDash = !mainDash.classList.contains('hidden') ? mainDash : adminDash;

    // Aplicamos el efecto visual de TV vieja
    activeDash.classList.add('tv-off');

    // Esperamos 400ms a que termine la animación antes de cambiar de pantalla
    setTimeout(() => {
        mainDash.classList.add('hidden');
        mainDash.classList.remove('flex');
        adminDash.classList.add('hidden');
        adminDash.classList.remove('flex');
        document.getElementById('analysis-modal').classList.add('hidden');
        document.getElementById('chat-window').classList.add('hidden');
        document.getElementById('user-input').value = '';
        document.getElementById('pass-input').value = '';
        document.getElementById('intro-screen').classList.remove('hidden');

        // IMPORTANTE: Quitamos la clase para que el dashboard esté normal la próxima vez
        activeDash.classList.remove('tv-off');
    }, 400); 
}


// ==========================================================
// 2. DASHBOARD DE USUARIO NORMAL (PLANTAS)
// ==========================================================

const plantDatabase = {
    'Manzanilla': { img: 'img/manzanilla.jpg', h: '65%', t: '24°C', ph: '6.8', uv: 'MODERADO' },
    'Sábila': { img: 'img/sabila.jpg', h: '38%', t: '28°C', ph: '7.2', uv: 'ALTO' },
    'Menta': { img: 'img/menta.jpg', h: '72%', t: '21°C', ph: '6.4', uv: 'BAJO' },
    'Lavanda': { img: 'img/lavanda.jpg', h: '50%', t: '23°C', ph: '6.7', uv: 'MODERADO' },
    'Cempasúchil': { img: 'img/cempasuchil.jpg', h: '60%', t: '25°C', ph: '6.9', uv: 'ALTO' },
    'Bugambilia': { img: 'img/bugambilia.jpg', h: '45%', t: '27°C', ph: '7.0', uv: 'ALTO' },
    'Toronjil': { img: 'img/toronjil.jpg', h: '68%', t: '22°C', ph: '6.5', uv: 'MODERADO' },
    'Peyote': { img: 'img/peyote.jpg', h: '15%', t: '32°C', ph: '8.0', uv: 'EXTREMO' },
    'Hongos': { img: 'img/hongos.jpg', h: '90%', t: '18°C', ph: '5.8', uv: 'NULO' }
};

let hChart, tChart;
// Memoria global para los reportes
let systemReports = [];

// --- NUEVA FUNCIÓN: Animador de números estilo terminal ---
function animateValue(obj, start, end, duration, suffix) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start) + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// --- FUNCIÓN ACTUALIZADA: updatePlant ---
function updatePlant(name) {
    const db = JSON.parse(localStorage.getItem('moleia_plants')) || plantDatabase;
    const data = db[name] || db['Manzanilla'];
    const img = document.getElementById('main-img');
    
    img.style.opacity = '0';
    setTimeout(() => {
        img.src = data.img; 
        document.getElementById('plant-tag').innerText = name.toUpperCase();
        
        // Elementos de texto
        const hum = document.getElementById('txt-hum');
        const temp = document.getElementById('txt-temp');
        
        // Extraemos solo los números para la animación
        const targetH = parseInt(data.h);
        const targetT = parseInt(data.t);

        // ¡Magia! Animamos desde 0 hasta el valor real en 600 milisegundos
        animateValue(hum, 0, targetH, 600, '%');
        animateValue(temp, 0, targetT, 600, '°C');
        
        document.getElementById('txt-ph').innerText = data.ph;
        document.getElementById('txt-uv').innerText = data.uv;

        // Si los valores son críticos (Override), los pintamos de rojo parpadeante
        if(data.h === '5%' || data.h === '10%') {
            hum.classList.add('text-red-500', 'animate-pulse');
            temp.classList.add('text-red-500', 'animate-pulse');
        } else {
            hum.classList.remove('text-red-500', 'animate-pulse');
            temp.classList.remove('text-red-500', 'animate-pulse');
        }
        
        img.style.opacity = '1';
    }, 200);
    
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.innerText === name.toUpperCase()));
}


// ==========================================================
// 3. ASISTENTE BOTÁNICO (CON MEMORIA PERSISTENTE)
// ==========================================================

const defaultChat = `<div class="text-[#00ffaa] opacity-80">> CONEXIÓN ESTABLECIDA...</div>
<div class="text-[#f97316]">> MOLE-IA: Saludos, Operador. Sistema de apoyo en línea.</div>`;

function loadChatHistory() {
    const chatBox = document.getElementById('chat-messages');
    const savedChat = localStorage.getItem('moleia_chat_history');
    if (savedChat) {
        chatBox.innerHTML = savedChat;
    } else {
        chatBox.innerHTML = defaultChat;
        localStorage.setItem('moleia_chat_history', defaultChat);
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

function saveChatHistory() {
    const chatBox = document.getElementById('chat-messages');
    localStorage.setItem('moleia_chat_history', chatBox.innerHTML);
}

function toggleChat() {
    const chatWindow = document.getElementById('chat-window');
    chatWindow.classList.toggle('hidden');
    chatWindow.classList.toggle('flex');
    if (!chatWindow.classList.contains('hidden')) {
        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
    }
}

function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML += `<div class="text-white text-right">> USUARIO: ${msg}</div>`;
    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    saveChatHistory(); // Guardar avance

    const typingId = 'typing-' + Date.now();
    chatMessages.innerHTML += `<div id="${typingId}" class="text-[#00ffaa] opacity-50">> Procesando datos...<span class="animate-pulse">_</span></div>`;
    chatMessages.scrollTop = chatMessages.scrollHeight;

    setTimeout(() => {
        const typingElement = document.getElementById(typingId);
        if(typingElement) typingElement.remove();
        
        const botResponses = [
            "Analizando niveles... Sugiero aplicar composta purificada.",
            "Recuerda: Reduce la humedad para evitar pudrición.",
            "ALERTA: Fluctuación térmica detectada. Ajusta el micro-goteo.",
            "Registrando en bitácora. Buen trabajo."
        ];
        
        const randomRes = botResponses[Math.floor(Math.random() * botResponses.length)];
        chatMessages.innerHTML += `<div class="text-[#f97316]">> MOLE-IA: ${randomRes}</div>`;
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        saveChatHistory(); // Guardar respuesta
    }, 1500);
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('chat-input')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendChatMessage();
    });
});


// ==========================================================
// 4. FUNCIONES EXCLUSIVAS DEL ADMINISTRADOR (AZUL)
// ==========================================================

let adminChart1, adminChart2, adminChart3;

function initAdminCharts() {
    if(adminChart1) adminChart1.destroy();
    if(adminChart2) adminChart2.destroy();
    if(adminChart3) adminChart3.destroy();

    const chartStyle = {
        color: '#00e5ff', font: { family: 'Share Tech Mono' }
    };

    const ctx1 = document.getElementById('admin-chart-users').getContext('2d');
    adminChart1 = new Chart(ctx1, {
        type: 'doughnut',
        data: {
            labels: ['Activos', 'Inactivos', 'Suspendidos'],
            datasets: [{
                data: [12, 5, 2],
                backgroundColor: ['#00e5ff', '#005577', '#ff4444'],
                borderColor: '#000511',
                borderWidth: 2
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: chartStyle } } }
    });

    const ctx2 = document.getElementById('admin-chart-regs').getContext('2d');
    adminChart2 = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: ['LUN','MAR','MIE','JUE','VIE','SAB','DOM'],
            datasets: [{
                label: 'Nuevos Operadores', data: [1, 3, 2, 5, 4, 8, 6],
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

    const ctx3 = document.getElementById('admin-chart-plants').getContext('2d');
    adminChart3 = new Chart(ctx3, {
        type: 'radar',
        data: {
            labels: ['Humedad', 'Temp.', 'Nutrientes', 'Radiación UV', 'pH'],
            datasets: [{
                label: 'Nivel Global',
                data: [80, 70, 90, 40, 65],
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
}

function downloadAdminReport() {
    const users = JSON.parse(localStorage.getItem('moleia_users'));
    const totalUsers = Object.keys(users).length;
    const date = new Date().toLocaleString();

    const fileContent = `
====================================================
      REPORTE DEL SISTEMA MOLE-IA - MODO ADMIN
====================================================
FECHA DE EXTRACCIÓN: ${date}
SUPERVISOR A CARGO: ADMIN

--- ESTADÍSTICAS GLOBALES ---
TOTAL DE USUARIOS REGISTRADOS: ${totalUsers}
ESTADO DEL SERVIDOR: ONLINE
NIVEL DE RADIACIÓN EXTERNA: ESTABLE

--- RESUMEN DE CULTIVOS ---
- MANZANILLA: Crecimiento óptimo (Sector A)
- PEYOTE: Cuarentena preventiva (Sector B)
- HONGOS: Producción al 90% (Sector Subterráneo)

[FIN DEL REPORTE]
====================================================
    `;

    const blob = new Blob([fileContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MOLE-IA_REPORTE_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// ----------------------------------------------------
// (Gráficas del Modal de Usuario Normal)
// ----------------------------------------------------

function renderLogList() {
    const logContainer = document.getElementById('log-list');
    if(!logContainer) return;
    
    // Datos de ejemplo para el registro de eventos
    const logs = [
        { time: '12:45:22', event: 'SISTEMA', detail: 'Calibración biométrica finalizada', status: '[OK]' },
        { time: '11:30:10', event: 'ALERTA', detail: 'Humedad crítica detectada', status: '[WARN]' },
        { time: '10:00:00', event: 'RIEGO', detail: 'Activación de micro-goteo', status: '[ACTIVE]' },
    ];

    // Estructura en columnas (grid)
    let logHTML = `
        <div class="grid grid-cols-12 gap-4 text-[#00ffaa]/50 border-b border-[#00ffaa]/30 pb-2 mb-3 tracking-widest text-xs">
            <div class="col-span-2 font-bold">HORA</div>
            <div class="col-span-2 font-bold">EVENTO</div>
            <div class="col-span-6 font-bold">DETALLE</div>
            <div class="col-span-2 font-bold text-center">ESTADO</div>
        </div>
    `;

    logHTML += logs.map(log => {
        let statusClass = 'text-[#00ffaa]';
        if(log.status === '[WARN]') statusClass = 'text-red-500 animate-pulse font-bold';
        if(log.status === '[ACTIVE]') statusClass = 'text-[#f97316]';

        return `
            <div class="grid grid-cols-12 gap-4 border-b border-[#00ffaa]/10 py-3 hover:bg-[#00ffaa]/5 transition-colors">
                <div class="col-span-2 text-white font-bold opacity-80">${log.time}</div>
                <div class="col-span-2 text-white font-bold opacity-80">${log.event}</div>
                <div class="col-span-6 text-[#00ffaa] opacity-90">${log.detail}</div>
                <div class="col-span-2 text-center ${statusClass}">${log.status}</div>
            </div>
        `;
    }).join('');

    logContainer.innerHTML = logHTML;
}

function openModal() {
    document.getElementById('main-dashboard').classList.add('hidden');
    document.getElementById('analysis-modal').classList.remove('hidden');
    document.getElementById('analysis-modal').classList.add('flex');
    const ctxH = document.getElementById('chart-hum').getContext('2d');
    const ctxT = document.getElementById('chart-temp').getContext('2d');
    
    // Función creadora de opciones para personalizar el Tooltip y colores
    const getChartOptions = (color, labelText) => ({
        responsive: true, 
        maintainAspectRatio: false, 
        interaction: { mode: 'index', intersect: false }, 
        plugins: { 
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.85)', 
                titleColor: color, 
                bodyColor: '#ffffff', 
                titleFont: { family: 'Share Tech Mono', size: 14, weight: 'bold' },
                bodyFont: { family: 'Share Tech Mono', size: 14 },
                borderColor: color, 
                borderWidth: 1.5,
                cornerRadius: 0, 
                displayColors: false, 
                padding: 10,
                caretSize: 6,
                callbacks: {
                    label: function(context) {
                        return `${labelText}: ${context.parsed.y}`;
                    }
                }
            }
        },
        scales: {
            x: { 
                grid: { color: color === '#00ffaa' ? 'rgba(0, 255, 170, 0.1)' : 'rgba(249, 115, 22, 0.1)' }, 
                ticks: { color: color, font: { family: 'Share Tech Mono' } } 
            },
            y: { 
                grid: { color: color === '#00ffaa' ? 'rgba(0, 255, 170, 0.1)' : 'rgba(249, 115, 22, 0.1)' }, 
                ticks: { color: color, font: { family: 'Share Tech Mono' } } 
            }
        }
    });

    if (hChart) hChart.destroy(); if (tChart) tChart.destroy();
    
    // Gráfica de Humedad (Verde)
    hChart = new Chart(ctxH, { 
        type: 'line', 
        data: { 
            labels: ['00:00','04:00','08:00','12:00','16:00','20:00','24:00'],
            datasets: [{ 
                data: [65,68,75,60,55,62,65], 
                borderColor: '#00ffaa', 
                backgroundColor: 'rgba(0, 255, 170, 0.1)', 
                fill: true, 
                tension: 0.4, 
                pointRadius: 5, 
                pointHoverRadius: 8, 
                pointBackgroundColor: '#000000', 
                pointBorderColor: '#00ffaa',
                pointBorderWidth: 2
            }] 
        }, 
        options: getChartOptions('#00ffaa', 'Humedad') 
    });
    
    // Gráfica de Temperatura (Naranja)
    tChart = new Chart(ctxT, { 
        type: 'line', 
        data: { 
            labels: ['00:00','04:00','08:00','12:00','16:00','20:00','24:00'],
            datasets: [{ 
                data: [22,20,24,28,27,24,23], 
                borderColor: '#f97316', 
                stepped: true, 
                pointRadius: 5, 
                pointHoverRadius: 8, 
                pointBackgroundColor: '#000000', 
                pointBorderColor: '#f97316',
                pointBorderWidth: 2
            }] 
        }, 
        options: getChartOptions('#f97316', 'Temperatura') 
    });

    renderLogList();
}

function closeModal() {
    document.getElementById('analysis-modal').classList.add('hidden');
    document.getElementById('analysis-modal').classList.remove('flex');
    document.getElementById('main-dashboard').classList.remove('hidden');
}

setInterval(() => { 
    const c = document.getElementById('clock');
    if(c) c.innerText = new Date().toLocaleTimeString('en-GB'); 
}, 1000);

// ==========================================================
// 5. SISTEMAS DE SUPERVISOR (OVERRIDE Y ESCÁNER)
// ==========================================================

function initPlantsDB() {
    if (!localStorage.getItem('moleia_plants')) {
        localStorage.setItem('moleia_plants', JSON.stringify(plantDatabase));
    }
}
initPlantsDB();

function triggerOverride(type) {
    const db = JSON.parse(localStorage.getItem('moleia_plants'));
    
    if (type === 'sequia') {
        db['Peyote'].h = '5%';
        db['Peyote'].t = '48°C';
        db['Peyote'].uv = 'LETAL';
        alert("ALERTA: Sequía extrema inducida en el sector PEYOTE.");
    } else if (type === 'fallo_riego') {
        db['Sábila'].h = '10%';
        db['Sábila'].t = '40°C';
        db['Sábila'].ph = '3.1';
        alert("ALERTA: Fallo de riego inducido en el sector SÁBILA.");
    } else if (type === 'restaurar') {
        localStorage.setItem('moleia_plants', JSON.stringify(plantDatabase)); 
        alert("SISTEMAS RESTAURADOS: Cultivos operando con normalidad.");
        return;
    }
    
    localStorage.setItem('moleia_plants', JSON.stringify(db));
}

function runDiagnostic() {
    const term = document.getElementById('diagnostic-term');
    term.innerHTML = '';
    const db = JSON.parse(localStorage.getItem('moleia_plants'));
    
    const targets = ['Manzanilla', 'Peyote', 'Sábila', 'Cempasúchil'];
    
    let lines = [
        "> INICIANDO PROTOCOLO DE DIAGNÓSTICO...",
        "> ESTABLECIENDO CONEXIÓN CON SENSORES...",
        "----------------------------------------"
    ];

    targets.forEach(plant => {
        const p = db[plant];
        const estado = parseInt(p.h) < 20 ? "<span class='text-red-500 animate-pulse'>CRÍTICO</span>" : "<span class='text-[#00ffaa]'>ÓPTIMO</span>";
        lines.push(`> [${plant.toUpperCase()}] Estado: ${estado}`);
        lines.push(`  | Humedad: ${p.h} | Temp: ${p.t} | Integ: ${parseInt(p.h) < 20 ? 'PELIGRO' : 'ESTABLE'} `);
    });

    lines.push("----------------------------------------");
    lines.push("> ESCANEO FINALIZADO.");

    let i = 0;
    const printInterval = setInterval(() => {
        if (i < lines.length) {
            term.innerHTML += `<li>${lines[i]}</li>`;
            term.parentElement.scrollTop = term.parentElement.scrollHeight; 
            i++;
        } else {
            clearInterval(printInterval);
        }
    }, 400); 
}

// ==========================================================
// 6. SISTEMA DE REPORTES Y BANDEJA DE ADMIN
// ==========================================================

function openContactModal() {
    document.getElementById('contact-modal').classList.remove('hidden');
    
    const loginInput = document.getElementById('user-input');
    const userField = document.getElementById('contact-user');
    
    if (loginInput && loginInput.value.trim() !== '') {
        userField.value = loginInput.value.toUpperCase();
    } else {
        userField.value = "OPERADOR_DESCONOCIDO";
    }
}

function closeContactModal() {
    document.getElementById('contact-modal').classList.add('hidden');
    document.getElementById('contact-status').classList.add('hidden');
    document.getElementById('contact-msg').value = ''; 
}

function sendReport() {
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

    setTimeout(() => {
        // Guardar en la memoria global
        const timestamp = new Date().toLocaleTimeString('en-GB');
        const user = document.getElementById('contact-user').value;
        const type = document.getElementById('contact-type').value;
        
        systemReports.push({ time: timestamp, user: user, type: type, message: msg });
        renderAdminReports(); // Dibuja el reporte en la bandeja del admin

        btnStatus.innerText = "TRANSMISIÓN EXITOSA. CENTRAL NOTIFICADA.";
        btnStatus.className = "text-center mt-4 text-xs font-bold text-[#00ffaa] tracking-widest";
        msgInput.value = ''; 
        
        setTimeout(() => { closeContactModal(); }, 2000);
    }, 1500); 
}

function renderAdminReports() {
    const container = document.getElementById('admin-reports-list');
    if(!container) return; 

    if(systemReports.length === 0) {
        container.innerHTML = `<div class="text-center opacity-50 text-xs py-8">> NO HAY REPORTES EN LA BANDEJA...</div>`;
        return;
    }

    // Dibujamos la lista con el reporte más nuevo hasta arriba
    container.innerHTML = [...systemReports].reverse().map(rep => `
        <div class="grid grid-cols-12 gap-4 text-xs border-b border-[#00e5ff]/10 py-3 px-2 hover:bg-[#00e5ff]/10 transition-colors">
            <div class="col-span-2 text-[#00e5ff]/70 font-bold">${rep.time}</div>
            <div class="col-span-3 text-white">${rep.user}</div>
            <div class="col-span-3 text-[#f97316] uppercase font-bold">${rep.type.replace('_', ' ')}</div>
            <div class="col-span-4 opacity-80 break-words">${rep.message}</div>
        </div>
    `).join('');
}

function generateMasterReport() {
    if(systemReports.length === 0) {
        alert("SISTEMA OVERRIDE: No hay registros para compilar.");
        return;
    }
    
    let reportText = "==========================================\n";
    reportText += "   MOLE-IA | REPORTE MAESTRO DE ANOMALÍAS \n";
    reportText += "==========================================\n\n";
    reportText += `FECHA DE EXTRACCIÓN: ${new Date().toLocaleDateString('en-GB')} - ${new Date().toLocaleTimeString('en-GB')}\n\n`;
    
    systemReports.forEach(r => {
        reportText += `[${r.time}] | OPERADOR: ${r.user} | CLASIFICACIÓN: ${r.type.toUpperCase().replace('_', ' ')}\n`;
        reportText += `>> REPORTE: ${r.message}\n`;
        reportText += `------------------------------------------\n`;
    });
    
    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MOLE_IA_REPORTE_${Date.now()}.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// --- COPIA DESDE AQUÍ ---
function backToIntro() {
    // 1. Ocultamos el login
    const loginScreen = document.getElementById('login-screen');
    loginScreen.classList.add('hidden');
    
    // 2. Mostramos la pantalla de inicio (donde está el botón [ INICIAR SISTEMA ])
    const introScreen = document.getElementById('intro-screen');
    introScreen.classList.remove('hidden');
    
    // 3. Limpiamos los campos y errores por si acaso
    document.getElementById('user-input').value = '';
    document.getElementById('pass-input').value = '';
    document.getElementById('login-error').classList.add('hidden');
}
// --- HASTA AQUÍ ---
