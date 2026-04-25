import * as userDashboard from './modules/auth/userDashboard.js';
import * as adminDashboard from './modules/auth/adminDashboard.js';
import * as i18n from './modules/ui/i18n.js';
import * as dom from './modules/ui/dom.js';
import * as history from './modules/ui/history.js';
import * as menus from './modules/ui/menus.js';
import * as security from './modules/ui/security.js';
import * as memory from './modules/ui/memory.js';
import * as iot from './modules/ui/iot.js';
import * as config from './modules/api/config.js';
import * as apiService from './modules/api/apiService.js';
import * as mlops from './modules/services/mlops.js';
import * as vision from './modules/services/vision.js';
import * as privacy from './modules/ui/privacy.js';
import * as reports from './modules/services/reports.js';
import * as chat from './modules/services/chat.js';
import * as supervisor from './modules/services/supervisor.js';
import * as crops from './modules/services/crops.js';
import * as map from './modules/services/map.js';
import * as tactical from './modules/ui/tactical.js';

import { moleApi } from './modules/api/apiService.js';

// ==========================================================
// 0. EXPOSE GLOBAL FUNCTIONS TO WINDOW (for inline HTML handlers)
// ==========================================================
// Import JWT helpers from config and expose to window
import { getAuthToken, setAuthToken, clearAuthToken } from './modules/api/config.js';
window.getAuthToken = getAuthToken;
window.setAuthToken = setAuthToken;
window.clearAuthToken = clearAuthToken;

// Import updatePlant from crops and expose to window
import { updatePlant as doUpdatePlant } from './modules/services/crops.js';
window.updatePlant = doUpdatePlant;

// ==========================================================
// 0. CONFIGURACIÓN ESTRUCTURAL (MÓDULOS E IDIOMAS)
// ==========================================================
// MODULES: Solo para modales (pantallas completas ahora navegan físicamente)
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

// Helper: create a DOM node with optional classes, textContent and attributes
function createNode(tag = 'div', className = '', text = '', attrs = {}) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = text;
    Object.keys(attrs || {}).forEach(k => {
        if (k === 'id') el.id = attrs[k];
        else if (k.startsWith('data-')) el.setAttribute(k, attrs[k]);
        else el.setAttribute(k, attrs[k]);
    });
    return el;
}

// Función para mostrar modales (no pantallas completas - esas navegan físicamente)
function showModule(moduleKey) {
    // Solo modales - pantallas completas navegan con window.location.href
    const modalScreens = ['analysis', 'contact', 'addPlant', 'loading', 'diagnosis', 'history', 'map', 'iot', 'profile', 'delete'];
    
    if (modalScreens.includes(moduleKey)) {
        // Ocultar otros modales primero
        modalScreens.forEach(key => {
            const el = document.getElementById(MODULES[key]);
            if (el) el.classList.add('hidden');
        });
        
        const target = document.getElementById(MODULES[moduleKey]);
        if (target) {
            target.classList.remove('hidden');
            target.classList.add('flex');
        }
        
        // Inicializaciones específicas por modal
        switch(moduleKey) {
            case 'map':
                if (typeof mapInstance !== "undefined" && mapInstance) setTimeout(() => mapInstance.invalidateSize(), 250);
                if (typeof fetchMapData === 'function') fetchMapData();
                break;
        }
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
    output.textContent = ''; 
    clearInterval(typeInterval); 
    let currentText = "", i = 0;
    
    typeInterval = setInterval(() => {
        currentText += text.charAt(i);
        output.textContent = currentText;
        const cursor = document.createElement('span');
        cursor.className = 'animate-pulse';
        cursor.textContent = '_';
        output.appendChild(cursor);
        i++;
        if (i === text.length) clearInterval(typeInterval);
    }, 20);
}

// Ensure typeContent is accessible from inline handlers
window.typeContent = typeContent;

// Small compatibility shims for UI buttons - now using physical navigation
function openUserCreationModal() {
    window.location.href = '/login.html?view=register';
}

function openAdminAddPlantModal() {
    window.location.href = '/admin.html';
}

function returnToOverride() {
    window.location.href = '/admin.html';
}

function startSystem() {
    window.location.href = '/login.html';
}

function showRegisterScreen() {
    window.location.href = '/login.html?view=register';
}


// --- REGISTRO ---
async function submitRegistration() {
    const userInput = document.getElementById('reg-user-input');
    const passInput = document.getElementById('reg-pass-input');
    const passConfirmInput = document.getElementById('reg-pass-confirm-input');
    
    const user = userInput?.value.trim() || '';
    const pass = passInput?.value.trim() || '';
    const passConfirm = passConfirmInput?.value.trim() || '';
    
    const errorMsg = document.getElementById('reg-error');
    const successMsg = document.getElementById('reg-success');

    if (errorMsg) errorMsg.classList.add('hidden');
    if (successMsg) successMsg.classList.add('hidden');

    if (user.length < 3 || pass.length < 3) {
        if (errorMsg) {
            errorMsg.innerText = "ERROR: MÍNIMO 3 CARACTERES.";
            errorMsg.classList.remove('hidden');
        }
        return;
    }
    if (pass !== passConfirm) {
        if (errorMsg) {
            errorMsg.innerText = "ERROR: LAS CONTRASEÑAS NO COINCIDEN.";
            errorMsg.classList.remove('hidden');
        }
        return;
    }
    if (user.toLowerCase() === 'admin') {
        if (errorMsg) {
            errorMsg.innerText = "ERROR: NOMBRE RESERVADO POR EL SISTEMA.";
            errorMsg.classList.remove('hidden');
        }
        return;
    }

    try {
        // USO DE API SERVICE: Endpoint real 'auth/register/'
        const response = await moleApi.post('auth/register/', { 
            username: user, 
            password: pass 
        });

        if (successMsg) {
            successMsg.innerText = `USUARIO "${user.toUpperCase()}" CREADO EN SERVIDOR.`;
            successMsg.classList.remove('hidden');
        }
        setTimeout(() => window.location.href = '/login.html', 2000); 

    } catch (error) {
        if (errorMsg) {
            errorMsg.innerText = error.message || "ERROR: NO SE PUDO CONECTAR AL SERVIDOR.";
            errorMsg.classList.remove('hidden');
        }
    }
}

// --- LOGIN REAL CON BYPASS TEMPORAL ---
async function attemptLogin() {
    const userInput = document.getElementById('user-input');
    const passInput = document.getElementById('pass-input');
    const user = userInput?.value.trim() || '';
    const pass = passInput?.value.trim() || '';
    const errorMsg = document.getElementById('login-error');
    
    if (errorMsg) errorMsg.classList.add('hidden');

    // Bypass rápido para pruebas UI
    if (user === 'dev' && pass === 'dev') {
        console.warn("> MODO DEV ACTIVADO: Entrando sin backend.");
        localStorage.setItem('moleia_current_user', user);
        localStorage.setItem('moleia_user_role', 'admin');
        window.location.href = '/admin.html';
        return;
    }

    if (!user || !pass) {
        if (errorMsg) {
            errorMsg.innerText = "ERROR: DEBE INGRESAR USUARIO Y CONTRASEÑA.";
            errorMsg.classList.remove('hidden');
        }
        return;
    }

    try {
        // USO DE API SERVICE: Endpoint real 'auth/login/'
        const userData = await moleApi.post('auth/login/', { 
            username: user, 
            password: pass 
        });

        // El ApiService guarda el JWT automáticamente. Si la API devuelve el token en otra llave, ajustamos:
        const token = userData.token || userData.access || userData.access_token;
        if (token) {
            await moleApi.setToken(token);
            localStorage.setItem('moleia_current_user', user);
            localStorage.setItem('moleia_user_role', user.toLowerCase() === 'admin' ? 'admin' : 'user');
            const role = user.toLowerCase() === 'admin' ? 'admin' : 'user';
            window.location.href = role === 'admin' ? '/admin.html' : '/dashboard.html';
        } else {
            throw new Error("Token no recibido desde el servidor.");
        }

    } catch (error) {
        console.warn("> Servidor rechazó credenciales o está offline.", error);
        if (errorMsg) {
            errorMsg.innerText = "ACCESO DENEGADO. CREDENCIALES INVÁLIDAS.";
            errorMsg.classList.remove('hidden');
        }
    }
}

// --- CIERRE DE SESIÓN ---
function logout() {
    // Purga de memoria y sesión
    try { window.clearAuthToken(); } catch (e) { if (moleApi && typeof moleApi.clearToken === 'function') moleApi.clearToken(); }
    localStorage.removeItem('moleia_current_user'); 
    localStorage.removeItem('moleia_user_role');
    
    if (typeof detachChatListener === 'function') detachChatListener(); 
    if (window.monitorInterval) clearInterval(window.monitorInterval);  

    console.log("> SESIÓN CERRADA: Memoria purgada y procesos detenidos.");
    
    // Navegación física al inicio
    window.location.href = '/index.html';
}

function backToDashboard() {
    window.location.href = '/dashboard.html';
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
    if (!dropdown) return;
    
    const currentUser = localStorage.getItem('moleia_current_user') || 'AGENTE MOLE';
    const dropdownUserName = document.getElementById('dropdown-user-name');
    if (dropdownUserName) dropdownUserName.innerText = currentUser.toUpperCase();

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
    const wizardContainer = document.getElementById('iot-wizard-modal');
    const wizardContent = wizardContainer?.querySelector('.border-2');
    if (!wizardContainer || !wizardContent) return;
    
    wizardContent.textContent = '';
    
    const h2 = document.createElement('h2');
    h2.className = 'text-xl font-bold tracking-widest uppercase text-[#00ffaa] border-b border-[#00ffaa]/30 pb-2 mb-4';
    h2.textContent = '> ENLACE DE HARDWARE: ESP32_NODE';
    wizardContent.appendChild(h2);

    if (step === 2) {
        const stepDiv = document.createElement('div');
        stepDiv.id = 'iot-step-2';
        stepDiv.className = 'iot-step block';

        const p1 = document.createElement('p');
        p1.className = 'text-white/80 text-sm mb-4';
        p1.textContent = '> Estableciendo protocolo de enlace Handshake con ESP32...';
        stepDiv.appendChild(p1);

        const progressContainer = document.createElement('div');
        progressContainer.className = 'w-full bg-black border border-[#00ffaa]/30 h-4 mb-4 mt-8 relative overflow-hidden';
        const progressFill = document.createElement('div');
        progressFill.id = 'iot-progress';
        progressFill.className = 'bg-[#00ffaa] h-full w-0 transition-all duration-1000 ease-out';
        progressContainer.appendChild(progressFill);
        stepDiv.appendChild(progressContainer);

        const pStatus = document.createElement('p');
        pStatus.id = 'iot-status-text';
        pStatus.className = 'text-center text-xs text-[#00ffaa] animate-pulse';
        pStatus.textContent = 'Sincronizando claves de telemetría...';
        stepDiv.appendChild(pStatus);

        wizardContent.appendChild(stepDiv);

        const closeBtn = document.createElement('button');
        closeBtn.setAttribute('data-action', 'modal:close-iot');
        closeBtn.className = 'absolute top-4 right-4 text-red-500 hover:text-red-400 font-bold';
        closeBtn.textContent = '[X]';
        wizardContent.appendChild(closeBtn);

        setTimeout(() => {
            const iotProgress = document.getElementById('iot-progress');
            if (iotProgress) iotProgress.style.width = '35%';
        }, 500);
        setTimeout(() => {
            const iotProgress = document.getElementById('iot-progress');
            const iotStatusText = document.getElementById('iot-status-text');
            if (iotProgress) iotProgress.style.width = '75%';
            if (iotStatusText) iotStatusText.textContent = 'Calibrando sensores analógicos...';
        }, 2000);
        
        setTimeout(() => nextIotStep(3), 4000);
        
    } else if (step === 3) {
        const stepDiv = document.createElement('div');
        stepDiv.id = 'iot-step-3';
        stepDiv.className = 'iot-step block text-center';

        const iconContainer = document.createElement('div');
        iconContainer.className = 'w-16 h-16 rounded-full border-4 border-[#00ffaa] flex items-center justify-center mx-auto mb-4 bg-[#00ffaa]/20 shadow-[0_0_20px_rgba(0,255,170,0.5)]';
        const svgNS = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(svgNS, 'svg');
        svg.setAttribute('class', 'w-8 h-8 text-[#00ffaa]');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('viewBox', '0 0 24 24');
        const path = document.createElementNS(svgNS, 'path');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        path.setAttribute('stroke-width', '3');
        path.setAttribute('d', 'M5 13l4 4L19 7');
        svg.appendChild(path);
        iconContainer.appendChild(svg);
        stepDiv.appendChild(iconContainer);

        const pTitle = document.createElement('p');
        pTitle.className = 'text-[#00ffaa] font-bold text-lg mb-2';
        pTitle.textContent = '¡CONEXIÓN ESTABLECIDA!';
        stepDiv.appendChild(pTitle);

        const pDesc = document.createElement('p');
        pDesc.className = 'text-white/70 text-xs mb-6';
        pDesc.textContent = 'El hardware AgroGuard ESP32 ahora está emparejado y listo para transmitir.';
        stepDiv.appendChild(pDesc);

        const finalBtn = document.createElement('button');
        finalBtn.setAttribute('data-action', 'iot:finalize');
        finalBtn.className = 'w-full border border-[#00ffaa] bg-[#00ffaa]/10 text-[#00ffaa] py-2 hover:bg-[#00ffaa] hover:text-black transition-colors font-bold text-sm';
        finalBtn.textContent = '> FINALIZAR PROTOCOLO';
        stepDiv.appendChild(finalBtn);

        wizardContainer.appendChild(stepDiv);

        const closeBtn = document.createElement('button');
        closeBtn.setAttribute('data-action', 'iot:finalize');
        closeBtn.className = 'absolute top-4 right-4 text-red-500 hover:text-red-400 font-bold';
        closeBtn.textContent = '[X]';
        wizardContainer.appendChild(closeBtn);
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
    const newUserPlants = document.getElementById('new-user-plants');
    if (newUserPlants) {
        newUserPlants.classList.add('hidden');
        newUserPlants.classList.remove('flex');
    }

    // 3. Transformamos el Dashboard Central
    const videoPlaceholder = document.getElementById('video-placeholder');
    const mainImg = document.getElementById('main-img');
    const plantTag = document.getElementById('plant-tag');
    
    if (videoPlaceholder) videoPlaceholder.classList.add('hidden'); // Quitamos el texto de espera
    if (mainImg) mainImg.classList.remove('hidden'); // Mostramos la imagen de la planta
    if (plantTag) plantTag.innerText = finalName; // Ponemos el nombre que eligió el usuario

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
// AbortController for the active flora search request (ensures cancellation of previous requests)
let floraSearchAbortController = null;

function loadFloraSearch() {
    console.debug('[Router] loadFloraSearch invoked');
    const container = document.getElementById('typewriter-output');
    if (!container) return;

    // 1. Detener cualquier animación de tipeo zombi que esté corriendo
    if (typeof typeInterval !== 'undefined') clearInterval(typeInterval);

    // 2. Inyectar la interfaz del buscador estilo Terminal
    container.textContent = '';
    
    const wrapper = document.createElement('div');
    wrapper.className = 'flex flex-col h-full w-full min-h-[200px]';
    
    const topBar = document.createElement('div');
    topBar.className = 'flex items-center border-b border-[#00ffaa]/50 pb-2 mb-4';
    
    const promptSpan = document.createElement('span');
    promptSpan.className = 'mr-2 animate-pulse';
    promptSpan.textContent = '>_';
    topBar.appendChild(promptSpan);
    
    const inputField = document.createElement('input');
    inputField.type = 'text';
    inputField.id = 'flora-search-input';
    inputField.className = 'bg-transparent border-none outline-none text-[#00ffaa] font-mono w-full placeholder-[#00ffaa]/30';
    inputField.placeholder = 'Buscar espécimen (ej. Agave, Cempasúchil)...';
    inputField.autocomplete = 'off';
    topBar.appendChild(inputField);
    
    wrapper.appendChild(topBar);
    
    const resultsDiv = document.createElement('div');
    resultsDiv.id = 'flora-search-results';
    resultsDiv.className = 'flex-1 overflow-y-auto pr-2 space-y-3 scrollbar-thin';
    
    const waitingText = document.createElement('p');
    waitingText.className = 'text-[#00ffaa]/50 text-sm italic';
    waitingText.textContent = 'Esperando consulta de base de datos...';
    resultsDiv.appendChild(waitingText);
    
    wrapper.appendChild(resultsDiv);
    container.appendChild(wrapper);

    // 3. Activar el campo de texto y el listener con Debounce (300ms)
    const input = document.getElementById('flora-search-input');
    input.focus();

    // Ensure any previous pending abort controller is canceled (defensive)
    if (floraSearchAbortController) {
        try { floraSearchAbortController.abort(); } catch (err) { /* ignore */ }
        floraSearchAbortController = null;
    }

    // Input listener uses debounce; responses are tied to an AbortController in searchPlant
    const onInput = (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        const resultsContainer = document.getElementById('flora-search-results');

        if (query.length < 2) {
            resultsContainer.textContent = '';
            const hint = document.createElement('p');
            hint.className = 'text-[#00ffaa]/50 text-sm italic';
            hint.textContent = 'Ingrese al menos 2 caracteres...';
            resultsContainer.appendChild(hint);
            return;
        }

        resultsContainer.textContent = '';
        const loading = document.createElement('p');
        loading.className = 'text-[#00ffaa] text-sm animate-pulse';
        loading.textContent = 'Consultando servidor central...';
        resultsContainer.appendChild(loading);

        searchTimeout = setTimeout(() => {
            searchPlant(query);
        }, 300);
    };

    // Remove any previous identical listener to avoid duplicates
    input.removeEventListener('input', input._floraListener || (() => {}));
    input.addEventListener('input', onInput);
    input._floraListener = onInput;
}

async function searchPlant(query) {
    const resultsContainer = document.getElementById('flora-search-results');

    // Cancel any previous inflight request for flora search
    if (floraSearchAbortController) {
        try { floraSearchAbortController.abort(); } catch (err) { /* ignore */ }
        floraSearchAbortController = null;
    }

    // Defensive: ensure API base exists
    if (!window.AppConfig || !window.AppConfig.API_BASE_URL) {
        resultsContainer.textContent = '';
        const err = document.createElement('p');
        err.className = 'text-red-500 text-sm bg-red-500/10 p-2 border border-red-500/30';
        err.textContent = 'ERROR: API base URL no configurada.';
        resultsContainer.appendChild(err);
        return;
    }

    floraSearchAbortController = new AbortController();
    const signal = floraSearchAbortController.signal;

    try {
        const url = `${window.AppConfig.API_BASE_URL}/plants/search/?q=${encodeURIComponent(query)}`;

        const headers = { 'Content-Type': 'application/json' };
        const token = (typeof window.getAuthToken === 'function') ? window.getAuthToken() : null;
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(url, {
            method: 'GET',
            headers,
            signal
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        const results = Array.isArray(data) ? data : (data.results || []);

        renderPlantResults(results);
    } catch (error) {
        if (error.name === 'AbortError') {
            // Request was intentionally aborted; ignore silently
            return;
        }
        console.error('[Flora Search] Falla de enlace:', error);
        resultsContainer.textContent = '';
        const alertEl = document.createElement('p');
        alertEl.className = 'text-red-500 text-sm bg-red-500/10 p-2 border border-red-500/30';
        alertEl.textContent = 'ERROR: Falla de enlace con la base de datos botánica.';
        resultsContainer.appendChild(alertEl);
    } finally {
        // Clear controller reference so future searches can create a new one
        floraSearchAbortController = null;
    }
}

function renderPlantResults(results) {
    const container = document.getElementById('flora-search-results');
    container.textContent = '';

    if (!results || results.length === 0) {
        const none = document.createElement('p');
        none.className = 'text-[#00ffaa]/70 text-sm border border-[#00ffaa]/20 p-2';
        none.textContent = 'Ningún espécimen coincide con los parámetros.';
        container.appendChild(none);
        return;
    }

    // Helper to safely extract fields
    const safe = (plant, ...keys) => {
        for (const k of keys) {
            if (plant[k]) return String(plant[k]);
        }
        return '';
    };

    results.forEach(plant => {
        const name = safe(plant, 'name', 'nombre', 'common_name') || 'Desconocida';
        const scientific = safe(plant, 'scientific_name', 'nombre_cientifico') || '';
        const desc = safe(plant, 'description', 'descripcion') || 'Sin registro en la base de datos.';

        const card = document.createElement('div');
        card.className = 'border border-[#00ffaa]/30 p-3 bg-[#00ffaa]/5 hover:bg-[#00ffaa]/20 transition-all cursor-pointer';

        const title = document.createElement('h3');
        title.className = 'font-bold text-[#00ffaa] text-sm tracking-widest';
        title.textContent = name.toUpperCase();
        card.appendChild(title);

        if (scientific) {
            const sci = document.createElement('p');
            sci.className = 'text-xs text-[#00ffaa]/70 italic mb-2';
            sci.textContent = scientific;
            card.appendChild(sci);
        }

        const snippet = document.createElement('p');
        snippet.className = 'text-xs text-[#00ffaa]/90 opacity-80';
        snippet.style.display = '-webkit-box';
        snippet.style.webkitLineClamp = '2';
        snippet.style.webkitBoxOrient = 'vertical';
        snippet.style.overflow = 'hidden';
        snippet.textContent = desc;
        card.appendChild(snippet);

        // Build expanded view on demand and restore original when closed
        const buildExpanded = () => {
            // Clear card
            while (card.firstChild) card.removeChild(card.firstChild);

            const eTitle = document.createElement('h3');
            eTitle.className = 'font-bold text-[#00ffaa] text-sm tracking-widest border-b border-[#00ffaa]/30 pb-1 mb-2';
            eTitle.textContent = name.toUpperCase();
            card.appendChild(eTitle);

            if (scientific) {
                const eSci = document.createElement('p');
                eSci.className = 'text-xs text-[#00ffaa]/70 italic mb-2';
                eSci.textContent = scientific;
                card.appendChild(eSci);
            }

            const eDesc = document.createElement('p');
            eDesc.className = 'text-xs text-[#00ffaa] leading-relaxed';
            eDesc.textContent = desc;
            card.appendChild(eDesc);

            const closeBtn = document.createElement('button');
            closeBtn.className = 'mt-3 text-xs text-black bg-[#00ffaa] px-2 py-1 hover:bg-white w-full font-bold tracking-widest';
            closeBtn.textContent = '[ CERRAR FICHA ]';
            closeBtn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                // Rebuild original summary view
                while (card.firstChild) card.removeChild(card.firstChild);
                card.appendChild(title);
                if (scientific) card.appendChild(document.createElement('p'));
                card.appendChild(snippet);
                // Reattach the click to expand
                card.addEventListener('click', onCardClick);
            });

            card.appendChild(closeBtn);
        };

        const onCardClick = () => {
            // Prevent multiple attached listeners
            card.removeEventListener('click', onCardClick);
            buildExpanded();
        };

        card.addEventListener('click', onCardClick);
        container.appendChild(card);
    });
}

// Make modules globally available temporarily for smooth transition
Object.assign(window, userDashboard);
Object.assign(window, adminDashboard);
Object.assign(window, i18n);
Object.assign(window, dom);
Object.assign(window, history);
Object.assign(window, menus);
Object.assign(window, security);
Object.assign(window, memory);
Object.assign(window, iot);
Object.assign(window, config);
Object.assign(window, apiService);
Object.assign(window, mlops);
Object.assign(window, vision);
Object.assign(window, reports);
Object.assign(window, chat);
Object.assign(window, supervisor);
Object.assign(window, crops);
Object.assign(window, map);
Object.assign(window, tactical);

// ── Wire ApiService.showToast to Tactical Toast ──────────────────────────
// This replaces the legacy CSS-dependent toast with our design-system-native one.
if (window.ApiService) {
    window.ApiService.showToast = function(message, type) {
        const typeMap = { error: 'error', warn: 'warn', info: 'info', success: 'success' };
        window.showTacticalToast(message, typeMap[type] || 'info');
    };
}
