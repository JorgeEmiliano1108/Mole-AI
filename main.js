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

// --- NUEVA VERSIÓN DE ATTEMPT LOGIN CON ANIMACIONES PRIME Y SOPORTE MULTIUSUARIO ---
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

            const overlay = document.createElement('div');
            overlay.className = 'fixed inset-0 z-[9999] flex items-center justify-center bg-black';
            document.body.appendChild(overlay);

            const noise = document.createElement('div');
            noise.className = 'absolute inset-0';
            noise.style.backgroundImage = 'repeating-radial-gradient(circle at 17% 32%, #ffffff, #000000 0.001px)';
            noise.style.animation = 'pure-static 0.1s infinite';
            noise.style.opacity = '0.85';
            overlay.appendChild(noise);

            loginScreen.classList.add('hidden');

            setTimeout(() => {
                noise.remove(); 
                
                const msg = document.createElement('h1');
                msg.innerText = "> BIENVENIDO SUPERVISOR";
                msg.className = "text-[#00e5ff] font-bold text-3xl md:text-5xl tracking-[0.3em] uppercase drop-shadow-[0_0_15px_#00e5ff] animate-pulse text-center px-4";
                msg.style.fontFamily = "'Share Tech Mono', monospace";
                overlay.appendChild(msg);

                setTimeout(() => {
                    overlay.style.transition = 'opacity 0.8s ease';
                    overlay.style.opacity = '0';
                    
                    const adminDash = document.getElementById('admin-dashboard');
                    adminDash.classList.remove('hidden');
                    adminDash.classList.add('flex');
                    initAdminCharts(); 
                    renderAdminReports();

                    setTimeout(() => overlay.remove(), 800); 
                }, 2500);

            }, 1500); 
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

        // LÓGICA DE RUTEO: DAVID VS NUEVO USUARIO
                    const davidNav = document.getElementById('david-plants');
                    const newUserNav = document.getElementById('new-user-plants');

                    if (user === 'david@gmail.com') {
                        if (davidNav) { davidNav.classList.remove('hidden'); davidNav.classList.add('flex'); }
                        if (newUserNav) { newUserNav.classList.add('hidden'); newUserNav.classList.remove('flex'); }
                        updatePlant('Manzanilla'); // Cargamos datos de David
                    } else {
                        if (davidNav) { davidNav.classList.add('hidden'); davidNav.classList.remove('flex'); }
                        if (newUserNav) { newUserNav.classList.remove('hidden'); newUserNav.classList.add('flex'); }
                        setEmptyDashboardState(); // Cargamos estado vacío
                    }            
                    
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

// Efecto TV):
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

// Termina la función de los reportes que se cortó en tu mensaje
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

// ==========================================================
// 7. FUNCIONES PARA NUEVOS USUARIOS Y MODAL DE CULTIVOS
// ==========================================================

function setEmptyDashboardState() {
    // Ponemos los sensores en espera
    document.getElementById('txt-hum').innerText = '--%';
    document.getElementById('txt-temp').innerText = '--°C';
    document.getElementById('txt-ph').innerText = '--';
    document.getElementById('txt-uv').innerText = 'N/A';
    
    // Alerta de sin señal
    const plantTag = document.getElementById('plant-tag');
    plantTag.innerText = 'SIN SEÑAL';
    plantTag.classList.add('text-red-500', 'animate-pulse');
    plantTag.classList.remove('text-[#00ffaa]');
    
    // Apagamos botones extra
    const btnAnalysis = document.getElementById('btn-analysis');
    if(btnAnalysis) {
        btnAnalysis.innerText = 'ESPERANDO DATOS...';
        btnAnalysis.disabled = true;
        btnAnalysis.classList.add('opacity-50', 'cursor-not-allowed');
    }
    
    // Gráfico de la cámara vacía
    const mainImgContainer = document.getElementById('main-img');
    const parentContainer = mainImgContainer.parentElement;
    
    // Ocultamos la imagen original y ponemos un contenedor vacío
    mainImgContainer.style.display = 'none';
    
    // Si no existe el contenedor de "no señal", lo creamos
    if (!document.getElementById('no-signal-container')) {
        const noSignal = document.createElement('div');
        noSignal.id = 'no-signal-container';
        noSignal.className = "text-[#00ffaa] opacity-50 flex flex-col items-center justify-center w-full h-full min-h-[250px] border border-dashed border-[#00ffaa]/30";
        noSignal.innerHTML = `
            <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
            <p class="text-xs tracking-widest text-center">> VINCULE UN CULTIVO <br> PARA INICIAR MONITOREO</p>
        `;
        parentContainer.appendChild(noSignal);
    } else {
        document.getElementById('no-signal-container').style.display = 'flex';
    }
}

function openAddPlantModal() {
    document.getElementById('add-plant-modal').classList.remove('hidden');
}

function closeAddPlantModal() {
    document.getElementById('add-plant-modal').classList.add('hidden');
}

function registerNewPlant() {
    console.log("> Procesando inicialización de nuevo cultivo...");
    alert("[ OK ] Cultivo inicializado en la base de datos local.");
    closeAddPlantModal(); // Esta es la magia que cierra tu ventana
}

// Pequeño parche para cuando David inicia sesión, asegurarnos de que se vuelva a ver la imagen 
// (por si un usuario nuevo cerró sesión y luego entró David)
const originalUpdatePlant = updatePlant;
updatePlant = function(name) {
    const mainImg = document.getElementById('main-img');
    const noSignal = document.getElementById('no-signal-container');
    
    if (mainImg) mainImg.style.display = 'block';
    if (noSignal) noSignal.style.display = 'none';
    
    const btnAnalysis = document.getElementById('btn-analysis');
    if(btnAnalysis) {
        btnAnalysis.innerText = '[ ANÁLISIS DETALLADO ]';
        btnAnalysis.disabled = false;
        btnAnalysis.classList.remove('opacity-50', 'cursor-not-allowed');
    }

    originalUpdatePlant(name);
};

// ==========================================================
// 8. FLUJO DE DIAGNÓSTICO (CÁMARA Y DEEPSEEK)
// ==========================================================

async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 1. Mostrar la imagen en la tarjeta de resultados (preview)
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('scanned-image-preview').src = e.target.result;
    };
    reader.readAsDataURL(file);

    // 2. Mostrar pantalla de carga
    document.getElementById('loading-scan-modal').classList.remove('hidden');

    // 3. Preparar los datos para el POST
    const formData = new FormData();
    formData.append('image', file);
    // formData.append('user_id', currentOperatorId); // Si necesitas mandar el ID del usuario

    try {
        /* ========================================================
        AQUÍ VA TU CÓDIGO REAL PARA EL BACKEND:
        
        const response = await fetch('https://tu-api.com/api/v1/diagnose/', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        ========================================================
        */

        // Simulamos el tiempo de respuesta del servidor (3 segundos) y la respuesta de DeepSeek
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        const data = {
            species: "Solanum lycopersicum (Tomate)",
            status: "Infección por Oídio (Hongo) - Nivel Crítico",
            ph: "5.2 (Ligeramente ácido)",
            treatment: "Aislar espécimen inmediatamente. Aplicar fungicida a base de azufre o bicarbonato de sodio (1 cucharada por litro de agua) cada 7 días. Mejorar ventilación y reducir humedad ambiental al 50%."
        };

        // 4. Llenar la tarjeta de diagnóstico con los datos
        document.getElementById('diag-species').innerText = data.species;
        document.getElementById('diag-status').innerText = data.status;
        document.getElementById('diag-ph').innerText = data.ph;
        document.getElementById('diag-treatment').innerText = data.treatment;

    } catch (error) {
        console.error("Error en conexión con el motor IA:", error);
        document.getElementById('diag-species').innerText = "ERROR DE CONEXIÓN";
        document.getElementById('diag-status').innerText = "Fallo al contactar servidor DeepSeek.";
    } finally {
        // 5. Ocultar carga y mostrar resultado
        document.getElementById('loading-scan-modal').classList.add('hidden');
        document.getElementById('diagnosis-result-modal').classList.remove('hidden');
        
        // Limpiar el input para permitir volver a escanear la misma foto si se desea
        document.getElementById('camera-input').value = '';
    }
}

function closeDiagnosisModal() {
    document.getElementById('diagnosis-result-modal').classList.add('hidden');
}

// ==========================================================
// 9. FLUJO DE MI HUERTO (HISTORIAL Y FAVORITOS - API SIMULADA)
// ==========================================================

// Bases de datos locales simuladas (hasta que conectes tu backend real)
let userHistoryDB = [
    { id: "SCAN-001", date: "15/03/2026", species: "Solanum lycopersicum", status: "Infección por Oídio", ph: "5.2" },
    { id: "SCAN-002", date: "10/03/2026", species: "Aloe vera", status: "Óptimo", ph: "7.1" }
];
let userFavoritesDB = [];

// Variable para recordar qué pestaña estamos viendo
let currentTab = 'history'; 

function openHistoryModal() {
    document.getElementById('history-modal').classList.remove('hidden');
    // Simulamos la llamada GET /api/v1/history/ y GET /api/v1/favorites/
    fetchAndRenderHuerto(currentTab);
}

function closeHistoryModal() {
    document.getElementById('history-modal').classList.add('hidden');
}

function switchHistoryTab(tab) {
    currentTab = tab;
    
    // Estilos visuales de las pestañas
    const btnHist = document.getElementById('tab-history');
    const btnFav = document.getElementById('tab-favorites');
    
    if (tab === 'history') {
        btnHist.className = "text-[#00ffaa] border-b-2 border-[#00ffaa] px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
        btnFav.className = "text-[#00ffaa]/40 hover:text-[#00ffaa] border-b-2 border-transparent px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
    } else {
        btnFav.className = "text-[#f97316] border-b-2 border-[#f97316] px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
        btnHist.className = "text-[#00ffaa]/40 hover:text-[#00ffaa] border-b-2 border-transparent px-2 py-1 text-xs md:text-sm font-bold tracking-widest transition-all";
    }
    
    fetchAndRenderHuerto(tab);
}

async function fetchAndRenderHuerto(tab) {
    const container = document.getElementById('history-list-container');
    container.innerHTML = `<div class="text-center text-[#00ffaa] animate-pulse mt-10 text-xs tracking-widest">> SINCRONIZANDO CON BASE DE DATOS CENTRAL...</div>`;

    // 1. SIMULACIÓN DE PETICIÓN GET (Tarda medio segundo)
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const dataToRender = tab === 'history' ? userHistoryDB : userFavoritesDB;
    const accentColor = tab === 'history' ? '#00ffaa' : '#f97316';

    // 2. RENDERIZADO DE LAS CARDS
    if (dataToRender.length === 0) {
        container.innerHTML = `<div class="text-center text-white/50 mt-10 text-xs tracking-widest">> NO HAY REGISTROS EN ESTA CATEGORÍA.</div>`;
        return;
    }

    container.innerHTML = dataToRender.map(item => `
        <div class="border border-[${accentColor}]/30 bg-black p-4 flex flex-col md:flex-row justify-between md:items-center gap-4 hover:bg-[${accentColor}]/10 transition-colors">
            <div>
                <span class="text-[10px] text-white/50 border border-white/20 px-1">${item.id} | ${item.date}</span>
                <h3 class="text-[${accentColor}] font-bold mt-1 text-sm md:text-base uppercase">${item.species}</h3>
                <p class="text-xs text-white/80">Estado: <span class="${item.status === 'Óptimo' ? 'text-[#00ffaa]' : 'text-red-400'}">${item.status}</span> | pH: ${item.ph}</p>
            </div>
            <div class="flex gap-2 shrink-0">
                <button onclick="downloadReportPDF('${item.id}', this)" class="border border-[#00e5ff] text-[#00e5ff] px-3 py-1 text-[10px] uppercase font-bold hover:bg-[#00e5ff] hover:text-black transition-colors">
                    [ PDF ]
                </button>
            </div>
        </div>
    `).join('');
}

// ----------------------------------------------------
// REEMPLAZA ESTA FUNCIÓN DEL FLUJO 1
// ----------------------------------------------------
async function saveToFavorites() {
    const btn = event.target;
    const originalText = btn.innerText;
    
    btn.innerText = "[ ENVIANDO... ]";
    btn.classList.add('animate-pulse');

    // SIMULACIÓN DE POST /api/v1/favorites/
    await new Promise(resolve => setTimeout(resolve, 800));

    // Tomamos los datos de la tarjeta actual que el usuario está viendo
    const newFavorite = {
        id: "FAV-" + Math.floor(Math.random() * 1000),
        date: new Date().toLocaleDateString('en-GB'),
        species: document.getElementById('diag-species').innerText,
        status: document.getElementById('diag-status').innerText,
        ph: document.getElementById('diag-ph').innerText
    };

    // Lo metemos al arreglo local (hasta que tengas BD)
    userFavoritesDB.push(newFavorite);

    btn.innerText = "[ GUARDADO EN FAVORITOS ]";
    btn.classList.remove('animate-pulse', 'border-[#f97316]', 'text-[#f97316]', 'hover:bg-[#f97316]');
    btn.classList.add('border-green-500', 'text-green-500', 'hover:bg-green-500', 'cursor-not-allowed');
    btn.disabled = true; // Evitar multiples clicks
}

// ==========================================================
// 10. FLUJO DE GEOLOCALIZACIÓN (MAPA Y PERMISOS)
// ==========================================================

let mapInstance = null;
let userLocation = null;

// 1. Pedir permiso de ubicación EXACTA
function requestLocation() {
    if ("geolocation" in navigator) {
        
        // Aquí configuramos el GPS en modo "Francotirador" (Alta Precisión)
        const opcionesGPS = {
            enableHighAccuracy: true, // Obliga al dispositivo a usar el hardware GPS real
            timeout: 10000,           // Le da 10 segundos máximo para encontrar los satélites
            maximumAge: 0             // Le dice que no use ubicaciones viejas guardadas en memoria
        };

        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = { lat: position.coords.latitude, lng: position.coords.longitude };
                console.log("> UBICACIÓN EXACTA CAPTURADA:", userLocation);

                // Si el mapa ya está abierto, lo centramos en ti con un zoom súper cercano (nivel 16)
                if (mapInstance) {
                    mapInstance.setView([userLocation.lat, userLocation.lng], 16);
                }
            },
            (error) => {
                console.warn("> ACCESO A GPS DENEGADO O FALLIDO:", error.message);
            },
            opcionesGPS // Pasamos las opciones aquí
        );
    }
}

// 2. Abrir el modal y renderizar el mapa
function openMapModal() {
    document.getElementById('map-modal').classList.remove('hidden');
    
    // Si el mapa no se ha creado aún, lo inicializamos
    if (!mapInstance) {
        // Coordenadas iniciales (Ejemplo: Centro de México), Zoom nivel 5
        mapInstance = L.map('map-container').setView([23.6345, -102.5528], 5);

        // Capa de mapa oscuro (Estilo Terminal/Cyberpunk)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20,
            keepBuffer: 4, // Mantiene en memoria los cuadritos que ya cargó
            updateWhenZooming: false // Evita parpadeos mientras haces el gesto de zoom
        }).addTo(mapInstance);
    } else {
        // Si ya existe, le decimos a Leaflet que recalcule su tamaño porque estaba oculto
        setTimeout(() => mapInstance.invalidateSize(), 400);
    }

    // 3. Cargar los pines de historial
    loadMapPins();
}

function closeMapModal() {
    document.getElementById('map-modal').classList.add('hidden');
}

// 4. Dibujar los puntos de infección en el mapa
function loadMapPins() {
    // Aquí harías un GET /api/v1/history/ para sacar la lat/lng de cada planta
    // Por ahora usamos datos simulados para que veas cómo se ve
    const geoData = [
        { lat: 19.4326, lng: -99.1332, species: "Tomate (Oídio)", status: "Crítico", color: "#ef4444" }, // CDMX (Rojo)
        { lat: 20.6596, lng: -103.3496, species: "Sábila", status: "Óptimo", color: "#00ffaa" }, // Guadalajara (Verde)
        { lat: 25.6866, lng: -100.3161, species: "Maíz (Roya)", status: "Atención", color: "#f97316" } // Monterrey (Naranja)
    ];

    // Limpiar pines anteriores si es necesario (opcional)
    // mapInstance.eachLayer((layer) => { if (layer instanceof L.Marker) mapInstance.removeLayer(layer) });

    geoData.forEach(point => {
        // Creamos un pin de estilo "hacker" con CSS en lugar del pin azul aburrido de Google Maps
        const customPin = L.divIcon({
            className: 'custom-pin',
            html: `<div style="background-color:${point.color}; width:12px; height:12px; border-radius:50%; box-shadow: 0 0 15px ${point.color}; border: 1px solid white;"></div>`,
            iconSize: [12, 12],
            iconAnchor: [6, 6]
        });

        // Agregamos el pin y su cuadrito de información (Popup)
        L.marker([point.lat, point.lng], { icon: customPin })
            .addTo(mapInstance)
            .bindPopup(`
                <div style="background:#001105; color:#00ffaa; border:1px solid #00ffaa; padding:8px; font-family:monospace; min-width: 150px;">
                    <strong style="color:white; display:block; border-bottom:1px solid rgba(0,255,170,0.3); padding-bottom:4px; margin-bottom:4px; text-transform:uppercase;">
                        ${point.species}
                    </strong>
                    Estado: <span style="color:${point.color}">${point.status}</span>
                </div>
            `);
    });
}

// ==========================================================
// 11. FLUJO DE DESCARGA DE REPORTES (PDF BLOB)
// ==========================================================

async function downloadReportPDF(reportId, btnElement) {
    // 1. Cambiamos el estado del botón a "descargando"
    const originalText = btnElement.innerText;
    btnElement.innerText = "[ DESCARGANDO... ]";
    btnElement.classList.add('animate-pulse', 'bg-[#00e5ff]/20');

    try {
        /* ========================================================
        AQUÍ VA TU CÓDIGO REAL PARA EL BACKEND (Cuando esté listo):
        
        const response = await fetch(`https://tu-api.com/api/v1/reports/${reportId}/download`, {
            method: 'GET',
            // headers: { 'Authorization': 'Bearer ' + token } // Si usas tokens de sesión
        });
        
        if (!response.ok) throw new Error('Error al descargar el archivo');
        
        const blob = await response.blob();
        ======================================================== */

        // SIMULACIÓN DE API: Esperamos 1.5 segundos para fingir que descargamos
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Creamos un Blob falso simulando ser un PDF (Solo para la prueba visual)
        const pdfContent = "%PDF-1.4\n% Simulación de reporte fitosanitario para MOLE-IA...\n% Especie sana. Fin del reporte.";
        const blob = new Blob([pdfContent], { type: 'application/pdf' });

        // 2. MAGIA DE FRONTEND: Crear enlace invisible y forzar descarga
        const url = window.URL.createObjectURL(blob); // Crea una URL temporal en el navegador
        const a = document.createElement('a');        // Crea una etiqueta <a> invisible
        a.style.display = 'none';
        a.href = url;
        a.download = `MOLE_IA_Reporte_${reportId}.pdf`; // El nombre con el que se guardará el archivo
        
        document.body.appendChild(a);
        a.click(); // ¡Simulamos que el usuario le dio clic!
        
        // 3. Limpieza de memoria
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        console.error("> ERROR DE DESCARGA:", error);
        alert("[!] ERROR: No se pudo establecer conexión con el servidor para la descarga.");
    } finally {
        // 4. Regresamos el botón a la normalidad
        btnElement.innerText = originalText;
        btnElement.classList.remove('animate-pulse', 'bg-[#00e5ff]/20');
    }
}

// ==========================================================
// MENÚ DESPLEGABLE DE CULTIVOS (DROPDOWN)
// ==========================================================
function toggleCultivosMenu() {
    const dropdown = document.getElementById('dropdown-cultivos');
    dropdown.classList.toggle('hidden');
}

// Cierra el menú si das clic en cualquier otro lado de la pantalla
window.addEventListener('click', function(e) {
    const dropdown = document.getElementById('dropdown-cultivos');
    const isClickInside = e.target.closest('button[onclick="toggleCultivosMenu()"]');
    
    if (dropdown && !dropdown.classList.contains('hidden') && !isClickInside) {
        dropdown.classList.add('hidden');
    }
});


// ==========================================================
// SEGURIDAD S1: RENDERIZADO SEGURO DE CHAT (Anti-XSS)
// ==========================================================

// 1. Creador de mensajes genéricos (Usuario o Estado)
function appendChatMessage(container, role, text, opts = {}) {
    const msg = document.createElement('div');
    msg.className = `ai-message ${role} ${opts.extraClass ? opts.extraClass : ''}`;

    // Si trae imagen adjunta, la inyectamos seguro
    if (opts.withImage && opts.imageSrc) {
        const img = document.createElement('img');
        img.className = 'w-32 h-32 object-cover border-2 border-[#00ffaa] mb-2'; // Estilo hacker
        img.alt = 'Imagen escaneada';
        img.src = opts.imageSrc;
        msg.appendChild(img);
    }

    // Inyectamos el texto de forma segura
    const textNode = document.createElement('div');
    textNode.className = 'chat-text text-sm font-mono text-white/80';
    textNode.textContent = text || '';
    msg.appendChild(textNode);

    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
    return msg;
}

// 2. Creador de respuestas de la IA (Multilínea y Alertas Tácticas)
function appendMultilineBotMessage(container, answer, tacticalCount) {
    const wrapper = document.createElement('div');
    wrapper.className = 'ai-message bot border-l-2 border-[#00ffaa] pl-3 mb-4';

    // Si hay alerta de plaga, metemos el badge estilo militar
    if (tacticalCount > 0) {
        const badge = document.createElement('div');
        badge.className = 'text-red-500 font-bold border border-red-500 p-1 text-xs mb-2 inline-block';
        badge.textContent = `> ALERTA TÁCTICA: ${tacticalCount} detectada(s)`;
        wrapper.appendChild(badge);
    }

    // Procesamos línea por línea de la IA sin usar HTML crudo
    const lines = String(answer || '').split('\n');
    lines.forEach((line, idx) => {
        const p = document.createElement('p');
        p.textContent = line;
        p.className = "text-[#00ffaa] font-mono text-sm";
        wrapper.appendChild(p);
        
        if (idx < lines.length - 1) {
            const spacer = document.createElement('br');
            wrapper.appendChild(spacer);
        }
    });

    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
}

// ==========================================================
// SEGURIDAD S1: CONTROL DE MEMORIA Y LISTENERS
// ==========================================================

let chatListenerAttached = false;

// Conectar el oído del chat UNA SOLA VEZ
function attachChatListenerOnce() {
    if (chatListenerAttached) return;
    // Asumiendo que 'handleChatResponse' es la función que procesa la llegada del mensaje
    if (typeof handleChatResponse === 'function') {
        window.addEventListener('chatMessage', handleChatResponse);
        chatListenerAttached = true;
        console.log("> Listener de chat asegurado.");
    }
}

// Desconectar el oído para liberar memoria RAM
function detachChatListener() {
    if (!chatListenerAttached) return;
    if (typeof handleChatResponse === 'function') {
        window.removeEventListener('chatMessage', handleChatResponse);
        chatListenerAttached = false;
        console.log("> Listener de chat desconectado (Memoria liberada).");
    }
}

// Limpiar la basura cuando el usuario cierra o recarga la página
window.addEventListener('beforeunload', () => {
    detachChatListener();
    if (typeof monitorInterval !== 'undefined' && monitorInterval) {
        clearInterval(monitorInterval);
        console.log("> Intervalo de sensores destruido.");
    }
});


// ==========================================================
// MÓDULO IOT: WIZARD DE CONFIGURACIÓN ESP32
// ==========================================================

function openIotWizard() {
    // 1. Mostrar el modal
    document.getElementById('iot-wizard-modal').classList.remove('hidden');
    // 2. Reiniciar siempre al Paso 1
    nextIotStep(1);
}

function closeIotWizard() {
    document.getElementById('iot-wizard-modal').classList.add('hidden');
    
    // SEGURIDAD CRÍTICA: Limpiar contraseñas del DOM al cerrar
    document.getElementById('wifi-ssid').value = '';
    document.getElementById('wifi-pass').value = '';
    document.getElementById('wifi-pass').type = 'password'; // resetear vista
    console.log("> Buffer de credenciales Wi-Fi purgado por seguridad.");
}

function nextIotStep(stepNumber) {
    // Ocultar todos los pasos
    document.querySelectorAll('.iot-step').forEach(el => el.classList.add('hidden'));
    
    // Mostrar el paso solicitado
    document.getElementById(`iot-step-${stepNumber}`).classList.remove('hidden');

    // Si pasamos al paso 3 (Confirmación), copiamos el nombre del Wi-Fi para que el usuario lo revise
    if (stepNumber === 3) {
        const ssidValue = document.getElementById('wifi-ssid').value || 'RED_DESCONOCIDA';
        document.getElementById('confirm-ssid').textContent = ssidValue;
    }
}

function toggleWifiPassword() {
    const passInput = document.getElementById('wifi-pass');
    if (passInput.type === 'password') {
        passInput.type = 'text';
    } else {
        passInput.type = 'password';
    }
}

function startHardwareProvisioning() {
    // Vamos al paso de carga
    nextIotStep(4);
    document.getElementById('iot-close-btn').classList.add('hidden'); // Ocultar la X para que no aborten el proceso

    // Simulamos que tarda 3 segundos en conectarse al ESP32 y luego mostramos el Éxito
    setTimeout(() => {
        nextIotStep(5);
        document.getElementById('iot-close-btn').classList.remove('hidden'); // Devolver la X
        
        // Aquí en el futuro haríamos el fetch al backend real
        console.log("> Datos enviados al endpoint de aprovisionamiento IoT.");
    }, 3000);
}
