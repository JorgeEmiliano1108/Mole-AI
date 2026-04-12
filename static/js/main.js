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

// Función Maestra de Navegación (CORREGIDA)
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
        if (moduleKey === 'dashboard') target.classList.add('flex'); // Mantiene el flex
    }

    // EL SWITCH AHORA ESTÁ DENTRO DE LA FUNCIÓN, DONDE PERTENECE
    switch(moduleKey) {
        case 'dashboard':
            if (typeof syncUserPlants === 'function') syncUserPlants();
            if (typeof loadChatHistory === 'function') loadChatHistory();
            break;
        case 'admin':
            if (typeof initAdminCharts === 'function') initAdminCharts();
            break;
        case 'map':
            if (typeof mapInstance !== "undefined" && mapInstance) setTimeout(() => mapInstance.invalidateSize(), 250);
            if (typeof fetchMapData === 'function') fetchMapData();
            break;
    }
}

function closeModule(moduleKey) {
    const target = document.getElementById(MODULES[moduleKey]);
    if (target) target.classList.add('hidden');
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
// 1. SISTEMA DE LOGIN Y REGISTRO
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

// --- REGISTRO ---
async function submitRegistration() {
    const user = document.getElementById('reg-user-input').value.trim();
    const pass = document.getElementById('reg-pass-input').value.trim();
    const passConfirm = document.getElementById('reg-pass-confirm-input').value.trim(); 
    const errorMsg = document.getElementById('reg-error');
    const successMsg = document.getElementById('reg-success');

    errorMsg.classList.add('hidden');
    successMsg.classList.add('hidden');

    if (user.length < 3 || pass.length < 3) {
        errorMsg.innerText = "ERROR: MÍNIMO 3 CARACTERES.";
        errorMsg.classList.remove('hidden');
        return;
    }
    if (pass !== passConfirm) {
        errorMsg.innerText = "ERROR: LAS CONTRASEÑAS NO COINCIDEN.";
        errorMsg.classList.remove('hidden');
        return;
    }
    if (user.toLowerCase() === 'admin') {
        errorMsg.innerText = "ERROR: NOMBRE RESERVADO POR EL SISTEMA.";
        errorMsg.classList.remove('hidden');
        return;
    }

    try {
        // USO DE API SERVICE: Endpoint real 'auth/register/'
        const response = await window.moleApi.post('auth/register/', { 
            username: user, 
            password: pass 
        });

        successMsg.innerText = `USUARIO "${user.toUpperCase()}" CREADO EN SERVIDOR.`;
        successMsg.classList.remove('hidden');
        setTimeout(() => showModule('login'), 2000); 

    } catch (error) {
        errorMsg.innerText = error.message || "ERROR: NO SE PUDO CONECTAR AL SERVIDOR.";
        errorMsg.classList.remove('hidden');
    }
}

// --- LOGIN REAL CON BYPASS TEMPORAL ---
async function attemptLogin() {
    const user = document.getElementById('user-input').value.trim();
    const pass = document.getElementById('pass-input').value.trim();
    const errorMsg = document.getElementById('login-error');
    
    errorMsg.classList.add('hidden');

    // Bypass rápido para pruebas UI
    if (user === 'dev' && pass === 'dev') {
        console.warn("> MODO DEV ACTIVADO: Entrando sin backend.");
        executeLoginSequence('admin');
        return;
    }

    try {
        // USO DE API SERVICE: Endpoint real 'auth/login/'
        const userData = await window.moleApi.post('auth/login/', { 
            username: user, 
            password: pass 
        });

        // El ApiService guarda el JWT automáticamente. Si la API devuelve el token en otra llave, ajustamos:
        const token = userData.token || userData.access || userData.access_token;
        if (token) {
            await window.moleApi.setToken(token);
            executeLoginSequence(user); 
        } else {
            throw new Error("Token no recibido desde el servidor.");
        }

    } catch (error) {
        console.warn("> Servidor rechazó credenciales o está offline.", error);
        errorMsg.innerText = "ACCESO DENEGADO. CREDENCIALES INVÁLIDAS.";
        errorMsg.classList.remove('hidden');
    }
}

// --- SECUENCIA VISUAL DE INICIO DE SESIÓN ---
function executeLoginSequence(user) {
    localStorage.setItem('moleia_current_user', user);
    localStorage.setItem('moleia_user_role', user.toLowerCase() === 'admin' ? 'admin' : 'user');
    
    const loginScreen = document.getElementById('login-screen');

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
                
                showModule('admin');
                
                setTimeout(() => overlay.remove(), 800); 
            }, 1000); 
        }, 800); 
    } else {
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

                // Inicializamos el dashboard sin plantas
                resetDashboard();
                showModule('dashboard');

            }, 200);
        }, 200);
    }
    
    document.getElementById('user-input').value = '';
    document.getElementById('pass-input').value = '';
}

// --- ESTADO VACÍO DEL DASHBOARD ---
function resetDashboard() {
    const imgEl = document.getElementById('main-img');
    const plantTag = document.getElementById('plant-tag');
    
    if(imgEl) {
        imgEl.classList.add('hidden'); 
        const placeholder = document.getElementById('video-placeholder');
        if(placeholder) placeholder.classList.remove('hidden');
    }
    
    if(plantTag) plantTag.innerText = "SIN ASIGNAR";

    document.getElementById('txt-hum').innerText = "--%";
    document.getElementById('txt-temp').innerText = "--°C";
    document.getElementById('txt-ph').innerText = "--";
    document.getElementById('txt-uv').innerText = "ESPERANDO...";
}

// --- CIERRE DE SESIÓN ---
function logout() {
    const mainDash = document.getElementById('main-dashboard');
    const adminDash = document.getElementById('admin-dashboard');
    const activeDash = !mainDash.classList.contains('hidden') ? mainDash : adminDash;

    // Efecto TV al cerrar sesión
    activeDash.classList.add('tv-off');

    // Cerrar también el dropdown de perfil si estaba abierto
    const dropdown = document.getElementById('profile-dropdown');
    if(dropdown && !dropdown.classList.contains('hidden')){
        dropdown.classList.add('hidden');
        dropdown.classList.remove('flex');
    }

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

function backToDashboard() {
    showModule('dashboard');
}

// ==========================================================
// ANIMACIÓN EFECTO TV PARA MODALES
// ==========================================================
function openModalWithTV(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    // Mostramos el contenedor oscuro de fondo
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    // Buscamos la caja interior para animar esa
    const modalContent = modal.querySelector('.border-2');
    if (modalContent) {
        modalContent.classList.remove('tv-off');
        modalContent.classList.add('tv-on');
    }
}

function closeModalWithTV(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    const modalContent = modal.querySelector('.border-2');
    if (modalContent) {
        modalContent.classList.remove('tv-on');
        modalContent.classList.add('tv-off');
        
        // Esperamos a que acabe la animación (250ms) antes de ocultar el modal completo
        setTimeout(() => {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }, 250);
    } else {
        modal.classList.add('hidden');
    }
}

// ==========================================================
// TOGGLE VENTANA DE PERFIL (DROPDOWN EN HEADER)
// ==========================================================
function toggleProfileDropdown() {
    const dropdown = document.getElementById('profile-dropdown');
    
    const currentUser = localStorage.getItem('moleia_current_user') || 'AGENTE MOLE';
    document.getElementById('dropdown-user-name').innerText = currentUser.toUpperCase();

    if (dropdown.classList.contains('hidden')) {
        dropdown.classList.remove('hidden');
        dropdown.classList.add('flex', 'tv-on');
        dropdown.classList.remove('tv-off');
    } else {
        dropdown.classList.add('tv-off');
        dropdown.classList.remove('tv-on');
        setTimeout(() => {
            dropdown.classList.add('hidden');
            dropdown.classList.remove('flex');
        }, 200);
    }
}

// ==========================================================
// RELOJ EN VIVO (TIEMPO REAL)
// ==========================================================
function updateClock() {
    // Busca todos los elementos con el ID 'clock' (por si hay en admin y user)
    const clockElements = document.querySelectorAll('#clock');
    if (clockElements.length === 0) return;

    const now = new Date();
    // Formatea la hora para que siempre tenga 2 dígitos (ej. 09:05:02)
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    const timeString = `${hours}:${minutes}:${seconds}`;

    // Actualiza todos los relojes que encuentre en la pantalla
    clockElements.forEach(clock => {
        clock.innerText = timeString;
    });
}

// Inicia el reloj de inmediato para no esperar el primer segundo
updateClock();
// Configura el intervalo para que se actualice cada 1000 milisegundos (1 segundo)
setInterval(updateClock, 1000);


//Simulacion para ver pruebas//

// ==========================================================
// SISTEMA DE VINCULACIÓN ESP32 (IOT WIZARD)
// ==========================================================
function nextIotStep(step) {
    // Buscamos el contenedor interior del modal para cambiar su contenido
    const wizardContainer = document.getElementById('iot-wizard-modal').querySelector('.border-2');
    
    if (step === 2) {
        // PASO 2: SIMULACIÓN DE CONEXIÓN Y BARRA DE PROGRESO
        wizardContainer.innerHTML = `
            <h2 class="text-xl font-bold tracking-widest uppercase text-[#00ffaa] border-b border-[#00ffaa]/30 pb-2 mb-4">
                > ENLACE DE HARDWARE: ESP32_NODE
            </h2>
            <div id="iot-step-2" class="iot-step block">
                <p class="text-white/80 text-sm mb-4">> Estableciendo protocolo de enlace Handshake con ESP32...</p>
                
                <div class="w-full bg-black border border-[#00ffaa]/30 h-4 mb-4 mt-8 relative overflow-hidden">
                    <div id="iot-progress" class="bg-[#00ffaa] h-full w-0 transition-all duration-1000 ease-out"></div>
                </div>
                
                <p id="iot-status-text" class="text-center text-xs text-[#00ffaa] animate-pulse">Sincronizando claves de telemetría...</p>
            </div>
            <button onclick="closeModalWithTV('iot-wizard-modal')" class="absolute top-4 right-4 text-red-500 hover:text-red-400 font-bold">[X]</button>
        `;

        // Simulamos el avance de la barra de progreso
        setTimeout(() => document.getElementById('iot-progress').style.width = '35%', 500);
        setTimeout(() => {
            document.getElementById('iot-progress').style.width = '75%';
            document.getElementById('iot-status-text').innerText = "Calibrando sensores analógicos...";
        }, 2000);
        
        // Saltamos automáticamente al paso 3 después de 4 segundos
        setTimeout(() => nextIotStep(3), 4000);
        
    } else if (step === 3) {
        // PASO 3: CONEXIÓN EXITOSA
        wizardContainer.innerHTML = `
            <h2 class="text-xl font-bold tracking-widest uppercase text-[#00ffaa] border-b border-[#00ffaa]/30 pb-2 mb-4">
                > ENLACE DE HARDWARE: ESP32_NODE
            </h2>
            <div id="iot-step-3" class="iot-step block text-center">
                <div class="w-16 h-16 rounded-full border-4 border-[#00ffaa] flex items-center justify-center mx-auto mb-4 bg-[#00ffaa]/20 shadow-[0_0_20px_rgba(0,255,170,0.5)]">
                    <svg class="w-8 h-8 text-[#00ffaa]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
                </div>
                <p class="text-[#00ffaa] font-bold text-lg mb-2">¡CONEXIÓN ESTABLECIDA!</p>
                <p class="text-white/70 text-xs mb-6">El hardware AgroGuard ESP32 ahora está emparejado y listo para transmitir.</p>
                <button onclick="closeIotAndShowPlantBtn()" class="w-full border border-[#00ffaa] bg-[#00ffaa]/10 text-[#00ffaa] py-2 hover:bg-[#00ffaa] hover:text-black transition-colors font-bold text-sm">
                    > FINALIZAR PROTOCOLO
                </button>
            </div>
            <button onclick="closeIotAndShowPlantBtn()" class="absolute top-4 right-4 text-red-500 hover:text-red-400 font-bold">[X]</button>
        `;
    }
}

// Función especial para cerrar el modal de IOT y mostrar el botón de "+ VINCULAR CULTIVO"
function closeIotAndShowPlantBtn() {
    closeModalWithTV('iot-wizard-modal');
    const btnCultivo = document.getElementById('new-user-plants');
    if(btnCultivo) {
        btnCultivo.classList.remove('hidden');
        btnCultivo.classList.add('flex'); // Lo mostramos para que ahora pueda agregar la planta
    }
}

// ==========================================================
// SISTEMA DE CULTIVOS Y SIMULACIÓN DE SENSORES
// ==========================================================

// Variable para guardar el intervalo del monitor y poder detenerlo después
window.monitorInterval = null;

function registerNewPlant() {
    const plantNameInput = document.getElementById('new-plant-name').value.trim();
    const finalName = plantNameInput !== '' ? plantNameInput.toUpperCase() : 'ESPÉCIMEN DESCONOCIDO';

    // 1. Cerramos la ventana de agregar planta
    closeModalWithTV('add-plant-modal');
    
    // 2. Ocultamos el botón de agregar planta (porque ya agregamos una)
    document.getElementById('new-user-plants').classList.add('hidden');
    document.getElementById('new-user-plants').classList.remove('flex');

    // 3. Transformamos el Dashboard Central
    document.getElementById('video-placeholder').classList.add('hidden'); // Quitamos el texto de espera
    document.getElementById('main-img').classList.remove('hidden'); // Mostramos la imagen de la planta
    document.getElementById('plant-tag').innerText = finalName; // Ponemos el nombre que eligió el usuario

}
