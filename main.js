// ==========================================================
// 0. CONFIGURACIÓN ESTRUCTURAL (MÓDULOS E IDIOMAS)
// ==========================================================
const MODULES = {
    intro: 'intro-screen',
    login: 'login-screen',
    register: 'register-screen',
    dashboard: 'main-dashboard',
    admin: 'admin-dashboard',
    analysis: 'analysis-modal',
    contact: 'contact-modal',
    addPlant: 'add-plant-modal',
    loading: 'loading-scan-modal',
    diagnosis: 'diagnosis-result-modal',
    history: 'history-modal',
    map: 'map-modal',
    iot: 'iot-wizard-modal',
    profile: 'user-profile-modal',
    delete: 'delete-account-modal'
};

const translations = {
    es: {
        intro_subtitle: "M O N I T O R I N G  T O O L",
        btn_start: "[ INICIAR SISTEMA ]",
        nav_obj: "OBJETIVO", nav_vis: "VISIÓN", nav_flora: "FLORA MEXICANA", nav_about: "ACERCA DE LA WEB",
        st_hum: "HUMEDAD AMBIENTE", st_temp: "TEMPERATURA", st_ph: "pH DEL SUELO", st_uv: "ÍNDICE UV"
    },
    en: {
        intro_subtitle: "M O N I T O R I N G  S Y S T E M",
        btn_start: "[ START SYSTEM ]",
        nav_obj: "OBJECTIVE", nav_vis: "VISION", nav_flora: "MEXICAN FLORA", nav_about: "ABOUT WEB",
        st_hum: "AMBIENT HUMIDITY", st_temp: "TEMPERATURE", st_ph: "SOIL pH", st_uv: "UV INDEX"
    }
};

// Función Maestra de Navegación
function showModule(moduleKey) {
    const mainScreens = ['intro', 'login', 'register', 'dashboard', 'admin'];
    if (mainScreens.includes(moduleKey)) {
        mainScreens.forEach(key => {
            const el = document.getElementById(MODULES[key]);
            if (el) el.classList.add('hidden');
        });
    }
    const target = document.getElementById(MODULES[moduleKey]);
    if (target) {
        target.classList.remove('hidden');
        if (moduleKey === 'map' && window.map) setTimeout(() => window.map.invalidateSize(), 250);
    }
}

function closeModule(moduleKey) {
    const target = document.getElementById(MODULES[moduleKey]);
    if (target) target.classList.add('hidden');
}

// 2. EJECUCIÓN DE PROCESOS REALES SEGÚN MÓDULO
        switch(moduleKey) {
            case 'dashboard':
                // Sincroniza plantas y carga historial de chat desde el servidor
                if (typeof syncUserPlants === 'function') syncUserPlants();
                if (typeof loadChatHistory === 'function') loadChatHistory();
                break;
            case 'admin':
                // Carga estadísticas reales en las gráficas (Módulo 04)
                if (typeof initAdminCharts === 'function') initAdminCharts();
                break;
            case 'map':
                // Refresca el mapa y carga pines de la base de datos (Módulo 10)
                if (window.map) setTimeout(() => window.map.invalidateSize(), 250);
                if (typeof fetchMapData === 'function') fetchMapData();
                break;
        }

function changeLanguage(lang) {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            el.innerText = translations[lang][key];
        }
    });
}

// ==========================================================
// 1. SISTEMA DE LOGIN Y REGISTRO (HÍBRIDO: BACKEND + LOCAL)
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
    showModule('login'); 
    document.getElementById('login-error').classList.add('hidden');
    clearInterval(typeInterval);
}

function showRegisterScreen() {
    showModule('register'); 
    document.getElementById('reg-user-input').value = '';
    document.getElementById('reg-pass-input').value = '';
    document.getElementById('reg-error').classList.add('hidden');
    document.getElementById('reg-success').classList.add('hidden');
}

function backToLogin() {
    showModule('login'); 
}

// --- REGISTRO CONECTADO AL BACKEND ---
async function submitRegistration() {
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

    try {
        // Intento de registro en Backend real
        const response = await fetch('http://localhost:3000/api/registro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });

        if (!response.ok) throw new Error("Fallo en servidor");

        successMsg.innerText = `USUARIO "${user.toUpperCase()}" CREADO EN SERVIDOR.`;
        successMsg.classList.remove('hidden');

    } catch (error) {
        console.warn("> Servidor no detectado. Guardando en registro local (Offline).");
        // Fallback: Guardado Local si no hay backend
        const users = JSON.parse(localStorage.getItem('moleia_users')) || {};
        if (users[user]) {
            errorMsg.innerText = "ERROR: EL USUARIO YA EXISTE.";
            errorMsg.classList.remove('hidden');
        } else {
            users[user] = pass;
            localStorage.setItem('moleia_users', JSON.stringify(users));
            successMsg.innerText = `USUARIO "${user.toUpperCase()}" CREADO (LOCAL).`;
            successMsg.classList.remove('hidden');
        }
    }
}

// --- LOGIN HÍBRIDO (BACKEND O LOCAL) ---
async function attemptLogin() {
    const user = document.getElementById('user-input').value.trim();
    const pass = document.getElementById('pass-input').value.trim();
    const errorMsg = document.getElementById('login-error');
    
    errorMsg.classList.add('hidden');

    try {
        // 1. INTENTO DE CONEXIÓN CON BACKEND REAL
        const response = await fetch('http://localhost:3000/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass }) 
        });

        if (response.ok) {
            const userData = await response.json();
            localStorage.setItem('moleia_token', userData.token); 
            executeLoginSequence(user); // Despliega UI
        } else {
            errorMsg.innerText = "ACCESO DENEGADO. CREDENCIALES INVÁLIDAS.";
            errorMsg.classList.remove('hidden');
        }

    } catch (error) {
        // 2. FALLBACK LOCAL (Si el servidor está apagado o no hay internet)
        console.warn("> Error crítico de red. Iniciando protocolo de acceso local...");
        
        const localUsers = JSON.parse(localStorage.getItem('moleia_users')) || {};
        
        if (localUsers[user] && localUsers[user] === pass) {
            localStorage.setItem('moleia_token', 'offline-token-12345'); 
            executeLoginSequence(user); // Despliega UI
        } else {
            errorMsg.innerText = "ACCESO DENEGADO (OFFLINE). CREDENCIALES INVÁLIDAS.";
            errorMsg.classList.remove('hidden');
        }
    }
}

// --- SECUENCIA VISUAL DE INICIO DE SESIÓN ---
function executeLoginSequence(user) {
    localStorage.setItem('moleia_current_user', user);
    localStorage.setItem('moleia_user_role', user.toLowerCase() === 'admin' ? 'admin' : 'user');
    
    const loginScreen = document.getElementById('login-screen');

    // =========================================================
    // ANIMACIÓN PARA EL ADMIN (GLITCH)
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
                
                if(typeof initAdminCharts === 'function') initAdminCharts(); 
                // if(typeof renderAdminReports === 'function') renderAdminReports(); // Descomentar si existe

                setTimeout(() => overlay.remove(), 800); 
            }, 2500);
        }, 1500); 
    } 
    // =========================================================
    // ANIMACIÓN PARA EL USUARIO (TV VIEJA)
    // =========================================================
    else {
        loginScreen.style.transformOrigin = 'center';
        loginScreen.style.transition = 'transform 0.2s ease-in, filter 0.2s ease-in';
        loginScreen.style.filter = 'brightness(8) contrast(2)';
        loginScreen.style.transform = 'scale(1, 0.005)'; 
        
        setTimeout(() => {
            loginScreen.style.transform = 'scale(0, 0.005)'; 
            
            setTimeout(() => {
                loginScreen.classList.add('hidden');
                loginScreen.style.transform = '';
                loginScreen.style.filter = '';
                loginScreen.style.transition = '';

                setTimeout(() => {
                    const dashboard = document.getElementById('main-dashboard');
                    dashboard.classList.remove('hidden');
                    dashboard.classList.add('flex');
                    
                    dashboard.style.transformOrigin = 'center';
                    dashboard.style.transform = 'scale(0, 0.005)';
                    dashboard.style.filter = 'brightness(8) contrast(2)';
                    
                    void dashboard.offsetWidth; 

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
                        }, 250);
                    }, 200);
                }, 2500); 
            }, 200);
        }, 200);
    }
    
    document.getElementById('user-input').value = '';
    document.getElementById('pass-input').value = '';
}

// --- CIERRE DE SESIÓN ---
function logout() {
    const mainDash = document.getElementById('main-dashboard');
    const adminDash = document.getElementById('admin-dashboard');
    const activeDash = !mainDash.classList.contains('hidden') ? mainDash : adminDash;

    activeDash.classList.add('tv-off');

    setTimeout(() => {
        localStorage.removeItem('moleia_token');        
        localStorage.removeItem('moleia_current_user'); 
        localStorage.removeItem('moleia_user_role');    
        
        if (typeof detachChatListener === 'function') detachChatListener(); 
        if (window.monitorInterval) clearInterval(window.monitorInterval);  

        mainDash.classList.add('hidden');
        mainDash.classList.remove('flex');
        adminDash.classList.add('hidden');
        adminDash.classList.remove('flex');
        
        document.querySelectorAll('.modal, [id$="-modal"]').forEach(m => m.classList.add('hidden'));
        
        document.getElementById('user-input').value = '';
        document.getElementById('pass-input').value = '';

        document.getElementById('intro-screen').classList.remove('hidden');
        activeDash.classList.remove('tv-off');
        
        console.log("> SESIÓN CERRADA: Memoria purgada y procesos detenidos.");
    }, 400); 
}
