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

// Ensure typeContent is accessible from inline handlers and attach resilient listeners
window.typeContent = typeContent;

document.addEventListener('DOMContentLoaded', () => {
    // Ensure router-driven actions exist on these elements; if template lacks `data-action`, set a safe default.
    const map = { 'btn-objetivo': 'type:objetivo', 'btn-vision': 'type:vision', 'btn-flora': 'type:flora' };
    Object.keys(map).forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            if (!el.hasAttribute('data-action')) {
                el.setAttribute('data-action', map[id]);
            }
        }
    });
});

// Small compatibility shims for UI buttons referenced in templates but not defined
function openUserCreationModal() {
    if (typeof showRegisterScreen === 'function') return showRegisterScreen();
    if (typeof showModule === 'function') return showModule('register');
    console.warn('openUserCreationModal: no register UI available');
}

function openAdminAddPlantModal() {
    if (typeof openAddPlantModal === 'function') return openAddPlantModal();
    if (typeof showModule === 'function') return showModule('admin');
    console.warn('openAdminAddPlantModal: no add-plant UI available');
}

function returnToOverride() {
    if (typeof showModule === 'function') return showModule('admin');
    console.warn('returnToOverride: showModule not available');
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
        // Use centralized clearAuthToken helper (config.js) which delegates to moleApi or localStorage
        try { window.clearAuthToken(); } catch (e) { if (window.moleApi && typeof window.moleApi.clearToken === 'function') window.moleApi.clearToken(); }
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
            <h2 class="text-xl font-bold tracking-widest uppercase text-[#00e5ff] border-b border-[#00e5ff]/30 pb-2 mb-4">
                > ENLACE DE HARDWARE: ESP32_NODE
            </h2>
            <div id="iot-step-2" class="iot-step block">
                <p class="text-white/80 text-sm mb-4">> Estableciendo protocolo de enlace Handshake con ESP32...</p>
                
                <div class="w-full bg-black border border-[#00e5ff]/30 h-4 mb-4 mt-8 relative overflow-hidden">
                    <div id="iot-progress" class="bg-[#00e5ff] h-full w-0 transition-all duration-1000 ease-out"></div>
                </div>
                
                <p id="iot-status-text" class="text-center text-xs text-[#00e5ff] animate-pulse">Sincronizando claves de telemetría...</p>
            </div>
            <button data-action="modal:close-iot" class="absolute top-4 right-4 text-red-500 hover:text-red-400 font-bold">[X]</button>
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
            <h2 class="text-xl font-bold tracking-widest uppercase text-[#00e5ff] border-b border-[#00e5ff]/30 pb-2 mb-4">
                > ENLACE DE HARDWARE: ESP32_NODE
            </h2>
            <div id="iot-step-3" class="iot-step block text-center">
                <div class="w-16 h-16 rounded-full border-4 border-[#00e5ff] flex items-center justify-center mx-auto mb-4 bg-[#00e5ff]/20 shadow-[0_0_20px_rgba(0,255,170,0.5)]">
                    <svg class="w-8 h-8 text-[#00e5ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
                </div>
                <p class="text-[#00e5ff] font-bold text-lg mb-2">¡CONEXIÓN ESTABLECIDA!</p>
                <p class="text-white/70 text-xs mb-6">El hardware AgroGuard ESP32 ahora está emparejado y listo para transmitir.</p>
                <button data-action="iot:finalize" class="w-full border border-[#00e5ff] bg-[#00e5ff]/10 text-[#00e5ff] py-2 hover:bg-[#00e5ff] hover:text-black transition-colors font-bold text-sm">
                    > FINALIZAR PROTOCOLO
                </button>
            </div>
            <button data-action="iot:finalize" class="absolute top-4 right-4 text-red-500 hover:text-red-400 font-bold">[X]</button>
        `;
    }
}

// Función especial para cerrar el modal de IOT y mostrar el botón de "+ VINCULAR CULTIVO"
function closeIotAndShowPlantBtn() {
    closeModal('iot-wizard-modal');
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

// ==========================================================
// EVENT ROUTER CENTRALIZADO (PATRÓN DE DELEGACIÓN)
// ==========================================================
const ActionMap = {
    'type:objetivo': () => typeContent('objetivo'),
    'type:vision': () => typeContent('vision'),
    'type:flora': () => loadFloraSearch(),
    'system:start': () => startSystem(),
    'auth:login': () => attemptLogin(),
    'auth:forgot': () => typeof forgotPassword === 'function' && forgotPassword(),
    'nav:register': () => showRegisterScreen(),
    'mlops:train-rag': () => typeof trainRagModel === 'function' && trainRagModel(),
    'mlops:train-cnn': () => typeof trainCnnModel === 'function' && trainCnnModel(),
    'admin:create-operator': () => openUserCreationModal(),
    'admin:add-plant': () => openAdminAddPlantModal(),
    'nav:logout': () => logout(),
    'nav:return-override': () => returnToOverride(),
    'modal:close-iot': () => closeModal('iot-wizard-modal'),
    'iot:finalize': () => closeIotAndShowPlantBtn(),
    'report:download': (target) => handleReportDownload(target),
    'menu:toggle-cultivos': () => toggleCultivosMenu()
};

document.body.addEventListener('click', (event) => {
    // Buscamos si el elemento clickeado (o alguno de sus padres) tiene un data-action
    const target = event.target.closest('[data-action]');
    if (!target) return;

    const action = target.getAttribute('data-action');
    if (ActionMap[action]) {
        event.preventDefault();
        try {
            ActionMap[action](target);
        } catch (error) {
            console.error(`[Router] Fallo al ejecutar acción: ${action}`, error);
        }
    } else {
        console.warn(`[Router] Acción no registrada: ${action}`);
    }
});

// ==========================================================
// HANDLER PARA DESCARGA DE REPORTES VÍA ROUTER
// ==========================================================
async function handleReportDownload(btnElement) {
    if (!btnElement) return;

    const reportId = btnElement.getAttribute('data-report-id');
    if (!reportId) {
        console.error('[Router] Missing data-report-id attribute');
        return;
    }

    // Reutilizamos la función existente downloadReportPDF con el elemento button
    await downloadReportPDF(reportId, btnElement);
}

// ==========================================================
// BUSCADOR DE FLORA MEXICANA (INTEGRACIÓN REAL CON API)
// ==========================================================
let searchTimeout = null;

function loadFloraSearch() {
    console.debug('[Router] loadFloraSearch invoked');
    const container = document.getElementById('typewriter-output');
    if (!container) return;

    // 1. Detener cualquier animación de tipeo zombi que esté corriendo
    if (typeof typeInterval !== 'undefined') clearInterval(typeInterval);

    // 2. Inyectar la interfaz del buscador estilo Terminal
    container.innerHTML = `
        <div class="flex flex-col h-full w-full min-h-[200px]">
            <div class="flex items-center border-b border-[#00e5ff]/50 pb-2 mb-4">
                <span class="mr-2 animate-pulse">>_</span>
                <input type="text" id="flora-search-input" 
                       class="bg-transparent border-none outline-none text-[#00e5ff] font-mono w-full placeholder-[#00e5ff]/30" 
                       placeholder="Buscar espécimen (ej. Agave, Cempasúchil)..."
                       autocomplete="off">
            </div>
            <div id="flora-search-results" class="flex-1 overflow-y-auto pr-2 space-y-3 scrollbar-thin">
                <p class="text-[#00e5ff]/50 text-sm italic">Esperando consulta de base de datos...</p>
            </div>
        </div>
    `;

    // 3. Activar el campo de texto y el listener con Debounce (300ms)
    const input = document.getElementById('flora-search-input');
    input.focus();
    input.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        const resultsContainer = document.getElementById('flora-search-results');
        
        if (query.length < 2) {
            resultsContainer.innerHTML = '<p class="text-[#00e5ff]/50 text-sm italic">Ingrese al menos 2 caracteres...</p>';
            return;
        }

        resultsContainer.innerHTML = '<p class="text-[#00e5ff] text-sm animate-pulse">Consultando servidor central...</p>';
        
        searchTimeout = setTimeout(() => {
            searchPlant(query);
        }, 300);
    });
}

async function searchPlant(query) {
    const resultsContainer = document.getElementById('flora-search-results');
    try {
        // Petición a tu API real de Django
        const url = `${window.AppConfig.API_BASE_URL}/plants/search/?q=${encodeURIComponent(query)}`;
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                // Enviamos el token si el usuario está logueado, por si la API lo requiere
                'Authorization': window.getAuthToken() ? `Bearer ${window.getAuthToken()}` : ''
            }
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        // Soportar tanto arrays directos como paginación { results: [...] }
        const results = Array.isArray(data) ? data : (data.results || []);
        
        renderPlantResults(results);
    } catch (error) {
        console.error("[Flora Search] Falla de enlace:", error);
        resultsContainer.innerHTML = `<p class="text-red-500 text-sm bg-red-500/10 p-2 border border-red-500/30">ERROR: Falla de enlace con la base de datos botánica.</p>`;
    }
}

function renderPlantResults(results) {
    const container = document.getElementById('flora-search-results');
    container.innerHTML = '';

    if (results.length === 0) {
        container.innerHTML = '<p class="text-[#00e5ff]/70 text-sm border border-[#00e5ff]/20 p-2">Ningún espécimen coincide con los parámetros.</p>';
        return;
    }

    results.forEach(plant => {
        // Adaptación defensiva a los nombres de campo de tu modelo Django
        const name = plant.name || plant.nombre || plant.common_name || 'Desconocida';
        const scientific = plant.scientific_name || plant.nombre_cientifico || '';
        const desc = plant.description || plant.descripcion || 'Sin registro en la base de datos.';
        
        const card = document.createElement('div');
        card.className = 'border border-[#00e5ff]/30 p-3 bg-[#00e5ff]/5 hover:bg-[#00e5ff]/20 transition-all cursor-pointer';
        card.innerHTML = `
            <h3 class="font-bold text-[#00e5ff] text-sm tracking-widest">${name.toUpperCase()}</h3>
            ${scientific ? `<p class="text-xs text-[#00e5ff]/70 italic mb-2">${scientific}</p>` : ''}
            <p class="text-xs text-[#00e5ff]/90 opacity-80" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${desc}</p>
        `;
        
        card.addEventListener('click', () => {
            // Expansión rápida de la ficha técnica al hacer clic
            card.innerHTML = `
                <h3 class="font-bold text-[#00e5ff] text-sm tracking-widest border-b border-[#00e5ff]/30 pb-1 mb-2">${name.toUpperCase()}</h3>
                ${scientific ? `<p class="text-xs text-[#00e5ff]/70 italic mb-2">${scientific}</p>` : ''}
                <p class="text-xs text-[#00e5ff] leading-relaxed">${desc}</p>
                <button class="mt-3 text-xs text-black bg-[#00e5ff] px-2 py-1 hover:bg-white w-full font-bold tracking-widest">
                    [ CERRAR FICHA ]
                </button>
            `;
        });
        
        container.appendChild(card);
    });
}
