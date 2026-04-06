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
// Prevent concurrent login attempts to avoid race conditions
let loginInProgress = false;

function initUsers() {
    if (!localStorage.getItem('moleia_users')) {
        const defaultUsers = { 'admin': 'admin' };
        localStorage.setItem('moleia_users', JSON.stringify(defaultUsers));
    }
}
initUsers();
// Ensure sessionReady flag exists and is false until successful login
try { if (window.moleApi) window.moleApi.sessionReady = false; } catch (e) { /* ignore */ }

function typeContent(section) {
    const resultContainer = document.getElementById('ficha-result-container');
    if (resultContainer && !resultContainer.classList.contains('hidden')) {
        // Si hay una ficha abierta, volvemos a la vista de búsqueda antes de escribir el mensaje
        document.getElementById('ficha-result-container').classList.add('hidden');
        document.getElementById('ficha-result-container').classList.remove('flex');
        document.getElementById('search-container').classList.remove('hidden');
    }
    
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

// ==========================================================
// BUSCADOR DE FICHAS TÉCNICAS (NAVEGADOR DE CULTIVOS)
// ==========================================================
let _buscarFichaTimer = null;
async function buscarFicha() {
    if (_buscarFichaTimer) clearTimeout(_buscarFichaTimer);
    _buscarFichaTimer = setTimeout(async () => {
        const inputEl = document.getElementById('ficha-search-input');
        const term = inputEl.value.trim().toLowerCase();
        
        if (!term) return;
        
        const searchContainer = document.getElementById('search-container');
    const resultContainer = document.getElementById('ficha-result-container');
    
    searchContainer.classList.add('hidden');
    resultContainer.classList.remove('hidden');
    resultContainer.classList.add('flex');
    
    resultContainer.innerHTML = '<p class="text-[#00ffaa] font-mono animate-pulse mt-4">> CONSULTANDO BASE DE DATOS MUNDIAL...</p>';
    
    try {
        let fichaData = null;
        
        if (window.moleApi) {
            try {
                const query = encodeURIComponent(term);
                // GET request to real backend
                const data = await window.moleApi.get('plants/search/?q=' + query, { allowAnonymous: true, silent: true });
                if (data && !data.error) {
                    fichaData = data;
                }
            } catch (err) {
                console.warn("> API de fichas falló o encontró error 404.", err);
            }
        }
        
        if (fichaData && !fichaData.error) {
            // ISO/MoProSoft Traceability Log
            const traceId = 'TRX-' + Math.random().toString(36).substr(2, 9).toUpperCase();
            const traceLog = {
                trace_id: traceId,
                timestamp: new Date().toISOString(),
                event: 'BIOMETRIC_SCAN_RENDER',
                species: fichaData.nombre || term,
                status: 'SUCCESS',
                compliance: 'ISO_MOPROSOFT_AUDIT_LOG'
            };
            const logs = JSON.parse(localStorage.getItem('moleia_trace_logs') || '[]');
            logs.push(traceLog);
            localStorage.setItem('moleia_trace_logs', JSON.stringify(logs));
            console.log(">> [TRACE LOG GENERATED]:", JSON.stringify(traceLog));
            
            // Tinte verde ciberpunk con CSS filter
            const fallbackImg = 'https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&q=80&w=600&h=400';
            const plantImg = fichaData.image_url || fallbackImg;

            resultContainer.innerHTML = `
                <div class="border-b border-[#00ffaa]/50 pb-2 mb-4 flex justify-between items-center shrink-0">
                    <h3 class="text-xl md:text-2xl font-bold tracking-widest text-[#00ffaa] uppercase">> ${_escapeHtml(fichaData.nombre || term)}</h3>
                    <button onclick="cerrarFicha()" class="text-[#00ffaa] hover:text-red-500 font-bold tracking-widest">[X]</button>
                </div>
                <div class="flex-1 overflow-y-auto text-sm font-mono text-[#00ffaa] space-y-4 pr-2 custom-scrollbar">
                    
                    <!-- INICIO CONTENEDOR ESCANEO BIOMÉTRICO -->
                    <div class="relative w-full h-[220px] md:h-[260px] border border-[#00ffaa]/80 bg-black overflow-hidden group">
                        <!-- Imágen de base -->
                        <img src="${plantImg}" class="absolute inset-0 w-full h-full object-cover mix-blend-screen opacity-70" style="filter: brightness(0.7) sepia(1) hue-rotate(85deg) saturate(5) contrast(1.2);">
                        
                        <!-- Interferencia/Estática -->
                        <div class="absolute inset-0 bg-[#00ffaa]/5 pointer-events-none animate-pulse"></div>
                        
                        <!-- Scanlines Fijas -->
                        <div class="absolute inset-0 pointer-events-none" style="background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 255, 170, 0.1) 3px, rgba(0, 255, 170, 0.1) 4px);"></div>
                        
                        <!-- Grid Overlay -->
                        <div class="absolute inset-0 pointer-events-none" style="background-image: linear-gradient(rgba(0,255,170,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,170,0.15) 1px, transparent 1px); background-size: 20px 20px;"></div>
                        
                        <!-- Barra de Escaneo Animada -->
                        <div class="absolute top-0 left-0 w-full h-1 bg-[#00ffaa] opacity-90 animate-biometric-scan shadow-[0_0_8px_2px_rgba(0,255,170,0.8)]"></div>
                        
                        <!-- Esquinas de Retículas / Crosshairs -->
                        <div class="absolute top-4 left-4 w-6 h-6 border-t-2 border-l-2 border-[#00ffaa]"></div>
                        <div class="absolute top-4 right-4 w-6 h-6 border-t-2 border-r-2 border-[#00ffaa]"></div>
                        <div class="absolute bottom-4 left-4 w-6 h-6 border-b-2 border-l-2 border-[#00ffaa]"></div>
                        <div class="absolute bottom-4 right-4 w-6 h-6 border-b-2 border-r-2 border-[#00ffaa]"></div>
                        
                        <!-- Caja de Objetivo Central -->
                        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 sm:w-32 sm:h-32 border border-[#00ffaa]/40 bg-[#00ffaa]/5">
                            <div class="absolute -top-2 left-1/2 -translate-x-1/2 w-6 h-2 bg-[#00ffaa]/80"></div>
                            <div class="absolute -bottom-2 left-1/2 -translate-x-1/2 w-6 h-2 bg-[#00ffaa]/80"></div>
                            <div class="absolute top-1/2 -left-2 -translate-y-1/2 w-2 h-6 bg-[#00ffaa]/80"></div>
                            <div class="absolute top-1/2 -right-2 -translate-y-1/2 w-2 h-6 bg-[#00ffaa]/80"></div>
                        </div>

                        <!-- Datos Técnicos Superpuestos -->
                        <div class="absolute top-3 left-6 text-[9px] sm:text-[10px] text-[#00ffaa] font-bold bg-black/70 px-2 py-1 border border-[#00ffaa]/40 backdrop-blur-sm">
                            [ UID: ${traceId} ]
                        </div>
                        <div class="absolute bottom-3 left-6 text-[9px] sm:text-[10px] text-[#00ffaa] font-bold bg-black/70 px-2 py-1 border border-[#00ffaa]/40 backdrop-blur-sm animate-pulse">
                            [ BIOMASS IDX: ${(0.8 + Math.random()*0.15).toFixed(2)} ]<br>
                            [ HEALTH_CHK: NOMINAL ]
                        </div>
                        <div class="absolute top-3 right-6 text-[9px] sm:text-[10px] text-[#00ffaa] font-bold bg-black/70 px-2 py-1 text-right border border-[#00ffaa]/40 backdrop-blur-sm">
                            <span class="opacity-70">LAT:</span> ${ (Math.random() * 90).toFixed(4) }N<br>
                            <span class="opacity-70">LON:</span> ${ (Math.random() * 180).toFixed(4) }W
                        </div>
                        <div class="absolute bottom-3 right-6 flex items-center gap-1">
                            <div class="w-2 h-2 rounded-full bg-red-500 animate-[pulse_1s_ease-in-out_infinite]"></div>
                            <span class="text-[9px] sm:text-[10px] text-red-500 font-bold leading-none tracking-widest mt-0.5">REC</span>
                        </div>
                    </div>
                    <!-- FIN CONTENEDOR ESCANEO BIOMÉTRICO -->

                    <p class="text-white/80 opacity-90 leading-relaxed mt-4">${_escapeHtml(fichaData.descripcion || 'Registro clasificado, requiere Nivel de Acceso 4.')}</p>
                    <pre class="bg-[#001105] border border-[#00ffaa]/30 p-3 text-[#f97316] font-mono text-xs overflow-x-auto whitespace-pre-wrap">
:: PARÁMETROS ÓPTIMOS (TELEMETRÍA) ::
- HUMEDAD AMBIENTE: ${_escapeHtml(String(fichaData.humedad || 'Desconocido'))}
- TEMP. ESTIMADA:   ${_escapeHtml(String(fichaData.temperatura || 'Desconocida'))}
- PH DEL SUELO:     ${_escapeHtml(String(fichaData.ph || 'Análisis Pendiente'))}
- TOLERANCIA UV:    ${_escapeHtml(String(fichaData.uv || 'Advertencia: Exposición'))}
                    </pre>
                    <ul class="list-none space-y-1">
                        <li><span class="text-white opacity-50">>></span> Directiva Primaria: <span class="text-[#00ffaa]/80">${_escapeHtml(fichaData.recomendacion || 'Proceder con precaución agroquímica.')}</span></li>
                        <li><span class="text-white opacity-50">>></span> Nivel de Amenaza Fitopatológica: <span class="text-green-400">BAJO</span></li>
                    </ul>
                </div>
                <button onclick="cerrarFicha()" class="mt-4 border border-[#00ffaa]/50 py-3 w-full hover:bg-[#00ffaa] hover:text-black transition-all font-bold tracking-widest uppercase shrink-0">
                    [ <- VOLVER AL TERMINAL ]
                </button>
            `;
        } else {
            resultContainer.innerHTML = `
                <div class="flex-1 flex flex-col justify-center items-center text-center mt-10">
                    <span class="text-red-500 text-6xl mb-4 font-bold">!</span>
                    <p class="text-red-500 font-bold tracking-widest animate-pulse border border-red-500 p-4 bg-red-500/10 text-lg md:text-xl">
                        >> ERROR 404:<br>ESPECIE NO ENCONTRADA EN LOS ARCHIVOS.
                    </p>
                </div>
                <button onclick="cerrarFicha()" class="mt-auto border border-[#00ffaa]/50 py-3 w-full hover:bg-[#00ffaa] hover:text-black transition-all font-bold tracking-widest uppercase text-[#00ffaa] mb-2">
                    [ ABORTAR BÚSQUEDA ]
                </button>
            `;
        }
    } catch (error) {
        console.error("Error global en buscarFicha:", error);
        resultContainer.innerHTML = `
            <div class="flex-1 flex flex-col justify-center items-center mt-10">
                <div class="p-6 border-2 border-red-500 bg-red-500/10 text-red-500 animate-pulse font-bold tracking-widest text-center">
                    [ ERROR CRÍTICO AL CONSULTAR API DE FICHAS ]
                </div>
            </div>
            <button onclick="cerrarFicha()" class="mt-auto border border-[#00ffaa]/50 py-3 w-full hover:bg-[#00ffaa] hover:text-black transition-all font-bold tracking-widest uppercase text-[#00ffaa] mb-2">
                [ <- VOLVER ]
            </button>
        `;
    }
    }, 400); // Debounce de 400ms
}

function cerrarFicha() {
    document.getElementById('ficha-result-container').classList.add('hidden');
    document.getElementById('ficha-result-container').classList.remove('flex');
    document.getElementById('search-container').classList.remove('hidden');
    
    document.getElementById('typewriter-output').innerHTML = '';
    const inputEl = document.getElementById('ficha-search-input');
    inputEl.value = '';
    inputEl.focus();
}

function startSystem() {
    cerrarFicha();
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

async function submitRegistration() {
    const user = document.getElementById('reg-user-input').value.trim();
    const emailStr = document.getElementById('reg-email-input').value.trim();
    const pass = document.getElementById('reg-pass-input').value.trim();
    const errorMsg = document.getElementById('reg-error');
    const successMsg = document.getElementById('reg-success');

    errorMsg.classList.add('hidden');
    successMsg.classList.add('hidden');

    if (!user || !emailStr || !pass) {
        errorMsg.innerText = "ERROR: COMPLETAR TODOS LOS CAMPOS OBLIGATORIOS.";
        errorMsg.classList.remove('hidden');
        return;
    }

    if (user.length < 3 || pass.length < 3) {
        errorMsg.innerText = "ERROR: MÍNIMO 3 CARACTERES PARA USUARIO Y CONTRASEÑA.";
        errorMsg.classList.remove('hidden');
        return;
    }

    if (user.toLowerCase() === 'admin') {
        errorMsg.innerText = "ERROR: NOMBRE RESERVADO POR EL SISTEMA.";
        errorMsg.classList.remove('hidden');
        return;
    }

    try {
        if (!window.moleApi) throw new Error("API no disponible");
        
        const payload = { username: user, email: emailStr, password: pass };

        const data = await window.moleApi.post('auth/register/', payload, { allowAnonymous: true, silent: true });
        
        successMsg.innerText = 'USUARIO "' + (data.username ? data.username.toUpperCase() : user.toUpperCase()) + '" CREADO.';
        successMsg.classList.remove('hidden');
        
        // Auto-fill login screen if they go back
        document.getElementById('user-input').value = user;
        
    } catch (err) {
        if (err.data && err.data.error) {
            errorMsg.innerText = "ERROR: " + err.data.error.toUpperCase();
        } else {
            errorMsg.innerText = "ERROR: RED SATELITAL CAÍDA.";
        }
        errorMsg.classList.remove('hidden');
    }
}

// --- attemptLogin WITH REAL API CALL ---
async function attemptLogin() {
    const user = document.getElementById('user-input').value.trim();
    const pass = document.getElementById('pass-input').value.trim();
    const errorMsg = document.getElementById('login-error');

    errorMsg.classList.add('hidden');

    if (!window.moleApi) {
        errorMsg.innerText = "ERROR: ENLACE SATELITAL CAÍDO. BACKEND INACCESIBLE.";
        errorMsg.classList.remove('hidden');
        return;
    }

    if (loginInProgress) return;
    loginInProgress = true;

    try {
        // Zero-Trust: delegate authentication to Django API Gateway (allowAnonymous is CRITICAL to avoid NO_TOKEN on login)
        const data = await window.moleApi.post('auth/validate-token/', { username: user, password: pass }, { silent: true, allowAnonymous: true });

        // Extract token from common response shapes and ensure it's a string
        let token = null;
        if (data) {
            if (typeof data === 'string') {
                token = data;
            } else if (typeof data.access === 'string') {
                token = data.access;
            } else if (typeof data.token === 'string') {
                token = data.token;
            } else if (typeof data.access_token === 'string') {
                token = data.access_token;
            } else if (typeof data.token_raw === 'string') {
                token = data.token_raw;
            } else if (typeof data.token === 'object' && data.token) {
                token = data.token.key || data.token.token || null;
            } else if (typeof data.data === 'object' && data.data && typeof data.data.token === 'string') {
                token = data.data.token;
            }
        }

        // Only persist when we have a plain string token. Otherwise treat as failure.
        if (token && typeof token === 'string') {
            // Immediate hydration to avoid race: set in-memory and localStorage BEFORE any other consumers run
            try {
                if (window.moleApi) window.moleApi.authToken = token;
            } catch (e) { /* ignore */ }
            try { localStorage.setItem('mole_jwt', token); } catch (e) { /* ignore */ }

            // Persist via ApiService (keeps storages in sync and triggers any internal hooks)
            await window.moleApi.setToken(token);

            // Bucle de espera (polling) - prefer localStorage persistence
            let waitTime = 0;
            while (!localStorage.getItem('mole_jwt') && waitTime < 500) {
                await new Promise(res => setTimeout(res, 50));
                waitTime += 50;
            }

            // Verificar presencia de token: si la API no persistió el token, tratar como fallo
            if (!localStorage.getItem('mole_jwt')) {
                // rollback any partial hydration
                try { if (window.moleApi) window.moleApi.authToken = null; } catch(e){}
                try { localStorage.removeItem('mole_jwt'); } catch(e){}
                throw new Error('SESSION_NOT_STARTED');
            }

            // Validate token freshness
            if (window.moleApi.isTokenExpired()) {
                window.moleApi.clearToken();
                throw new Error('Sesión inválida o token expirado.');
            }

            // Bypass de Emergencia para EmiMole: No forzar hard-refresh, sino cargar el DOM explícito de admin
        }

        // Debug verification as requested
            // If login did not return a usable token, show error and stop here
            if (!token || typeof token !== 'string' || token.trim() === '') {
                errorMsg.innerText = "ACCESO DENEGADO. CREDENCIALES INVÁLIDAS.";
                errorMsg.classList.remove('hidden');
                return;
            }

            try { console.log("DEBUG: Token persistido ->", !!localStorage.getItem('mole_jwt')); } catch (e) { console.log('DEBUG: token persistence unknown'); }

            // HARDENING: clear persisted chat history after successful login
            try {
                localStorage.removeItem('moleia_chat_history');
            } catch (e) {
                console.warn('Could not clear moleia_chat_history on login:', e);
            }

            // Mark session as ready so UI components can safely perform protected requests
            try { if (window.moleApi) window.moleApi.sessionReady = true; } catch (e) { /* ignore */ }

        // Role assignment from backend
        let role = data.role || data.tipo || 'user';
        if (user === 'EmiMole') {
            role = 'admin'; // Forzar rol de admin explícitamente y cargar el dashboard
        }
        try { localStorage.setItem('moleia_role', role); } catch(e) {}
        const loginScreen = document.getElementById('login-screen');

        if (role === 'admin' || role === 'superuser') {
            if (!document.getElementById('admin-glitch-style')) {
                const style = document.createElement('style');
                style.id = 'admin-glitch-style';
                style.innerHTML = '@keyframes pure-static { 0% { background-position: 0% 0%; filter: invert(0%) sepia(100%) hue-rotate(180deg) saturate(500%); } 25% { background-position: 50% 50%; filter: invert(100%); } 50% { background-position: -20% 30%; filter: invert(0%); } 75% { background-position: 80% -10%; filter: invert(100%); } 100% { background-position: 100% 100%; filter: invert(0%); } }';
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

                    // Ensure charts/reports initialize after token persisted
                    try {
                        if (typeof initAdminCharts === 'function') initAdminCharts();
                        if (typeof renderAdminReports === 'function') renderAdminReports();
                        if (typeof pollLiveAlerts === 'function') pollLiveAlerts();
                    } catch (e) {
                        console.error('Error inicializando gráficas/informes:', e);
                    }

                    setTimeout(() => overlay.remove(), 800);
                }, 2500);

            }, 1500);
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

                    const davidNav = document.getElementById('david-plants');
                    const newUserNav = document.getElementById('new-user-plants');

                    if (user === 'david@gmail.com' || user === 'david') {
                        if (davidNav) { davidNav.classList.remove('hidden'); davidNav.classList.add('flex'); }
                        if (newUserNav) { newUserNav.classList.add('hidden'); newUserNav.classList.remove('flex'); }
                        // Load collection from backend and select default plant
                        loadMyCollection();
                    } else {
                        if (davidNav) { davidNav.classList.add('hidden'); davidNav.classList.remove('flex'); }
                        if (newUserNav) { newUserNav.classList.remove('hidden'); newUserNav.classList.add('flex'); }
                        setEmptyDashboardState();
                    }

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
                                loadChatHistory();
                            }, 250);
                        }, 200);

                    }, 2500);

                }, 200);
            }, 200);
        }

        document.getElementById('user-input').value = '';
        document.getElementById('pass-input').value = '';

    } catch (err) {
        console.warn('> Backend auth error:', err);

        if (err && err.message === 'NO_TOKEN') {
            errorMsg.innerText = "ERROR: NO SE PUDO ALMACENAR EL TOKEN. INTÉNTELO DE NUEVO.";
        } else if (err && (err.status === 401 || err.status === 403 || err.message === 'Sesión expirada. Vuelve a iniciar sesión.')) {
            errorMsg.innerText = "ACCESO DENEGADO. CREDENCIALES INVÁLIDAS.";
        } else {
            // Network Error / Timeout u otro issue del proxy
            errorMsg.innerText = "ERROR: ENLACE SATELITAL CAÍDO. BACKEND INACCESIBLE.";
        }

        errorMsg.classList.remove('hidden');
    } finally {
        // release login mutex
        loginInProgress = false;
    }
    }

function logout() {
    const mainDash = document.getElementById('main-dashboard');
    const adminDash = document.getElementById('admin-dashboard');
    const activeDash = !mainDash.classList.contains('hidden') ? mainDash : adminDash;

    activeDash.classList.add('tv-off');

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

        activeDash.classList.remove('tv-off');

        // Clear auth token on logout
        if (window.moleApi) { window.moleApi.clearToken(); }

        // GATING POR ROL: Limpiar intervalos de admin y rol
        try { clearInterval(window.telemetryIntervalId); window.telemetryIntervalId = null; } catch(e) {}
        try { clearInterval(window.notificationsIntervalId); window.notificationsIntervalId = null; } catch(e) {}
        try { localStorage.removeItem('moleia_role'); } catch(e) {}

        // MOPROSOFT/ISO DATA ISOLATION: Clear chat state on logout
        localStorage.removeItem('moleia_chat_history');
        const chatBox = document.getElementById('chat-messages');
        if (chatBox && typeof defaultChat !== 'undefined') {
            chatBox.innerHTML = defaultChat;
        } else if (chatBox) {
            chatBox.innerHTML = '<div class="text-[#00ffaa] opacity-80">> CONEXIÓN ESTABLECIDA...</div>\n<div class="text-[#f97316]">> MOLE-IA: Saludos, Operador. Sistema de apoyo en línea.</div>';
        }
    }, 400); 
}

// ==========================================================
// 2. DASHBOARD DE USUARIO NORMAL (PLANTAS) - Dynamic collection
// ==========================================================

let hChart, tChart;
let systemReports = [];

// Load the authenticated user's collection from backend and render buttons/cards
async function loadMyCollection() {
    const placeholder = document.getElementById('david-plants-placeholder');
    const nav = document.getElementById('david-plants');
    if (placeholder) placeholder.innerText = 'Cargando colección...';

    if (!window.moleApi || !window.moleApi.isTokenPresent()) {
        if (placeholder) placeholder.innerText = 'Sesión no iniciada. Inicia sesión para ver "Mi Colección".';
        return;
    }

    try {
        const plants = await window.moleApi.get('plants/my-collection/', { silent: true });

        if (!nav) return;
        nav.innerHTML = '';

        if (!plants || plants.length === 0) {
            nav.innerHTML = '<div class="text-xs text-[#00ffaa]/60">No hay cultivos vinculados.</div>';
            return;
        }

        plants.forEach(p => {
            const btn = document.createElement('button');
            btn.className = 'nav-btn';
            const label = (p.nickname || (p.species && (p.species.common_name || p.species.scientific_name)) || 'PLANTA').toUpperCase();
            btn.innerText = label;
            btn.onclick = () => updatePlant(p);
            nav.appendChild(btn);
        });

        // Select first plant by default
        updatePlant(plants[0]);
    } catch (err) {
        console.warn('> Falló carga de Mi Colección:', err && err.message);
        if (placeholder) placeholder.innerText = 'Error cargando colección.';
    }
}

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

function updatePlant(plant) {
    // Accept either a plant object (from backend) or a string name (legacy). Prefer object.
    let dataObj = null;
    let displayName = '';

    if (!plant) return;
    if (typeof plant === 'string') {
        displayName = plant;
    } else if (typeof plant === 'object') {
        dataObj = plant;
        displayName = (plant.nickname || (plant.species && (plant.species.common_name || plant.species.scientific_name)) || 'PLANTA');
    }

    const img = document.getElementById('main-img');
    img.style.opacity = '0';

    setTimeout(() => {
        if (dataObj && (dataObj.image_url || dataObj.img)) {
            img.src = dataObj.image_url || dataObj.img;
        }
        document.getElementById('plant-tag').innerText = displayName.toUpperCase();

        const hum = document.getElementById('txt-hum');
        const temp = document.getElementById('txt-temp');

        // If backend provides numeric values, use them; otherwise clear or keep previous.
        const humVal = dataObj && (dataObj.humidity || dataObj.soil_humidity || dataObj.h) ? dataObj.humidity || dataObj.soil_humidity || parseInt((dataObj.h || '').replace('%','')) : null;
        const tempVal = dataObj && (dataObj.temperature || dataObj.air_temperature || dataObj.t) ? dataObj.temperature || dataObj.air_temperature || parseInt((dataObj.t || '').replace('°C','')) : null;

        if (humVal !== null) animateValue(hum, 0, Math.round(humVal), 600, '%');
        if (tempVal !== null) animateValue(temp, 0, Math.round(tempVal), 600, '°C');

        if (dataObj && dataObj.ph) {
            document.getElementById('txt-ph').innerText = String(dataObj.ph);
        }
        if (dataObj && dataObj.uv_index !== undefined) {
            document.getElementById('txt-uv').innerText = String(dataObj.uv_index);
        }

        img.style.opacity = '1';
    }, 200);

    // Toggle active class on nav buttons by label
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.innerText === displayName.toUpperCase()));

    // If we have a plant id, fetch latest telemetry
    if (dataObj && dataObj.id) {
        updateTelemetry(dataObj.id);
    }
}

// Fetch latest telemetry for a plant and update DOM/charts
async function updateTelemetry(plantId) {
    if (!plantId) return;
    if (!window.moleApi || !window.moleApi.isTokenPresent()) return;

    try {
        const data = await window.moleApi.get('telemetry/latest/?plant_id=' + plantId, { silent: true });
        if (!data) return;

        // Update stat cards
        if (data.soil_humidity !== undefined && document.getElementById('txt-hum')) {
            document.getElementById('txt-hum').innerText = Math.round(data.soil_humidity) + '%';
        }
        if (data.air_temperature !== undefined && document.getElementById('txt-temp')) {
            document.getElementById('txt-temp').innerText = Math.round(data.air_temperature) + '°C';
        }
        if (data.ph_level !== undefined && document.getElementById('txt-ph')) {
            document.getElementById('txt-ph').innerText = String(data.ph_level);
        }
        if (data.uv_index !== undefined && document.getElementById('txt-uv')) {
            document.getElementById('txt-uv').innerText = String(data.uv_index);
        }

        // If modal charts are open, push the values to hChart/tChart (if present)
        try {
            if (hChart && Array.isArray(hChart.data.datasets[0].data)) {
                hChart.data.datasets[0].data.shift();
                hChart.data.datasets[0].data.push(data.soil_humidity || 0);
                hChart.update();
            }
            if (tChart && Array.isArray(tChart.data.datasets[0].data)) {
                tChart.data.datasets[0].data.shift();
                tChart.data.datasets[0].data.push(data.air_temperature || 0);
                tChart.update();
            }
        } catch (e) { /* silent */ }

    } catch (err) {
        console.warn('> Falló al obtener telemetría:', err && err.message);
    }
}

function changePlant(key) {
    const nameMap = {
        'manzanilla': 'Manzanilla', 'sabila': 'Sábila', 'menta': 'Menta',
        'lavanda': 'Lavanda', 'cempasuchil': 'Cempasúchil', 'bugambilia': 'Bugambilia',
        'toronjil': 'Toronjil', 'peyote': 'Peyote', 'hongos': 'Hongos'
    };
    updatePlant(nameMap[key] || 'Manzanilla');
}


// ==========================================================
// 3. ASISTENTE BOTÁNICO (CON CONEXIÓN REAL AL BACKEND)
// ==========================================================

const defaultChat = '<div class="text-[#00ffaa] opacity-80">> CONEXIÓN ESTABLECIDA...</div>\n<div class="text-[#f97316]">> MOLE-IA: Saludos, Operador. Sistema de apoyo en línea.</div>';

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

// --- sendChatMessage WITH REAL API CALL ---
function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML += '<div class="text-white text-right">> USUARIO: ' + _escapeHtml(msg) + '</div>';
    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    saveChatHistory();

    const typingId = 'typing-' + Date.now();
    chatMessages.innerHTML += '<div id="' + typingId + '" class="text-[#00ffaa] opacity-50">> Procesando datos...<span class="animate-pulse">_</span></div>';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Try real backend first
    if (window.moleApi) {
        // Ensure token is present before calling LLM endpoint. If missing, redirect to login.
        if (!window.moleApi.isTokenPresent() || window.moleApi.isTokenExpired()) {
            console.warn('> Chat request aborted: no valid token present. Redirecting to login.');
            // Force logout UI and avoid fallback to prevent leaking 401 attempts
            try { logout(); } catch(e) { /* silent */ }
            return;
        }

        window.moleApi.post('chat/fallback/', { question: msg })
            .then(function(data) {
                var el = document.getElementById(typingId);
                if (el) el.remove();

                var answer = (data && (data.answer || data.response)) || 'Sin respuesta del servidor.';
                chatMessages.innerHTML += '<div class="text-[#f97316]">> MOLE-IA: ' + _escapeHtml(answer) + '</div>';

                // COFEPRIS disclaimer in chat (tactical military style)
                if (data && data.disclaimer) {
                    chatMessages.innerHTML += '<div class="border-l-2 border-[#ff8c00] pl-2 mt-2 mb-2"><span class="text-[#ff8c00] font-bold text-[10px] tracking-widest">> ALERTA COFEPRIS:</span><br><span class="text-[#ff8c00]/80 text-[10px]">' + _escapeHtml(data.disclaimer) + '</span></div>';
                }

                chatMessages.scrollTop = chatMessages.scrollHeight;
                saveChatHistory();
            })
            .catch(function(err) {
                // If unauthorized, redirect to login instead of falling back
                if (err && (err.status === 401 || err.status === 403 || err.message === 'NO_TOKEN' || err.message === 'EXPIRED_TOKEN')) {
                    console.warn('> Chat request unauthorized. Redirecting to login.');
                    try { logout(); } catch(e) { /* silent */ }
                    return;
                }

                console.warn('> Chat backend no disponible, usando respuesta local:', err && err.message);
                _fallbackChatResponse(typingId, chatMessages);
            });
    } else {
        // No ApiService available — use local fallback
        setTimeout(function() { _fallbackChatResponse(typingId, chatMessages); }, 1500);
    }
}

function _fallbackChatResponse(typingId, chatMessages) {
    var el = document.getElementById(typingId);
    if (el) el.remove();
    
    var botResponses = [
        "Analizando niveles... Sugiero aplicar composta purificada.",
        "Recuerda: Reduce la humedad para evitar pudrición.",
        "ALERTA: Fluctuación térmica detectada. Ajusta el micro-goteo.",
        "Registrando en bitácora. Buen trabajo."
    ];
    
    var randomRes = botResponses[Math.floor(Math.random() * botResponses.length)];
    chatMessages.innerHTML += '<div class="text-[#f97316]">> MOLE-IA: ' + randomRes + '</div>';
    chatMessages.scrollTop = chatMessages.scrollHeight;
    saveChatHistory();
}

function sanitizeHTML(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/[&<>"']/g, function(match) {
        switch(match) {
            case '&': return '&amp;';
            case '<': return '&lt;';
            case '>': return '&gt;';
            case '"': return '&quot;';
            case "'": return '&#39;';
            default: return match;
        }
    });
}

function _escapeHtml(str) {
    return sanitizeHTML(str);
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('chat-input')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendChatMessage();
    });
    // If already authenticated, attempt to load user's collection
    if (window.moleApi && window.moleApi.isTokenPresent() && !window.moleApi.isTokenExpired()) {
        try { loadMyCollection(); } catch(e) { /* silent */ }
    }
    // Admin-only initializations: start telemetry polling and stats
    // only when the admin notifications feed is present in the DOM Y el rol es explícitamente admin.
    let isAdmin = false;
    try {
        const storedRole = localStorage.getItem('moleia_role');
        isAdmin = (storedRole === 'admin' || storedRole === 'superuser');
    } catch(e) {}
    
    if (document.getElementById('live-notifications-feed') && isAdmin) {
        try { fetchAdminStats(); } catch(e) { /* silent */ }
        try { pollLiveAlerts(); } catch(e) { /* silent */ }
    }
});

// COFEPRIS Disclaimer listener
window.addEventListener('disclaimerReceived', function(e) {
    var container = document.getElementById('disclaimer-container');
    if (!container) return;
    container.innerHTML = '<div class="disclaimer-banner" role="alert"><div class="disclaimer-header">[ ALERTA LEGAL DEL SISTEMA ]</div><div class="disclaimer-body">' + _escapeHtml(e.detail.text) + '</div><button class="disclaimer-dismiss" onclick="this.closest(\'.disclaimer-banner\').remove()">[ CERRAR ]</button></div>';
    container.classList.remove('hidden');
});

// ==========================================================
// 4. FUNCIONES EXCLUSIVAS DEL ADMINISTRADOR (AZUL)
// ==========================================================

let adminChart1, adminChart2, adminChart3;

// Helper: show an overlay error instead of drawing on canvas (stable across resizes)
function _showCanvasError(canvasId, message) {
    try {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        // hide canvas to avoid Chart.js redrawing over the message
        canvas.style.display = 'none';

        const parent = canvas.parentElement || canvas.parentNode;
        if (!parent) return;

        // Avoid duplicating overlay
        const overlayId = canvasId + '-error-overlay';
        let overlay = document.getElementById(overlayId);
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = overlayId;
            overlay.className = 'text-[#ff4444] font-mono animate-pulse font-bold flex items-center justify-center h-full text-center bg-black/50 border border-[#ff4444] p-4';
            overlay.style.minHeight = canvas.style.height || (canvas.height ? canvas.height + 'px' : '200px');
            overlay.style.width = '100%';
            overlay.style.boxSizing = 'border-box';
            parent.appendChild(overlay);
        }
        overlay.innerText = message;
        overlay.style.display = 'flex';
    } catch (e) {
        console.warn('Error mostrando overlay de canvas:', e);
    }
}

function _hideCanvasError(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas) canvas.style.display = 'block';
    const overlay = document.getElementById(canvasId + '-error-overlay');
    if (overlay) overlay.style.display = 'none';
}

function _showContainerError(containerId, message) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    const div = document.createElement('div');
    div.className = 'text-[#ff4444] font-mono animate-pulse font-bold flex items-center justify-center h-full text-center bg-black/50 border border-[#ff4444] p-4';
    div.innerText = message;
    container.appendChild(div);
}

function initAdminCharts() {
    // Zero-Trust: only fetch admin stats if a valid JWT exists in memory and role is admin
    let isAdmin = false;
    try {
        const r = localStorage.getItem('moleia_role');
        isAdmin = (r === 'admin' || r === 'superuser');
    } catch(e) {}

    if (!isAdmin || !window.moleApi || !window.moleApi.isTokenPresent() || window.moleApi.isTokenExpired()) {
        _showCanvasError('admin-chart-users', '> ERROR DE TELEMETRÍA: NO AUTORIZADO');
        _showCanvasError('admin-chart-regs', '> ERROR DE TELEMETRÍA: NO AUTORIZADO');
        _showCanvasError('admin-chart-plants', '> ERROR DE TELEMETRÍA: NO AUTORIZADO');
        return;
    }

    // Use dedicated fetch helper to centralize error handling and shape guarantees
    fetchAdminStats()
        .catch(err => {
            console.warn('> API admin/stats/ failed:', err && err.message);
            if (err && (err.status === 401 || err.status === 403)) {
                _showCanvasError('admin-chart-users', '> ERROR DE TELEMETRÍA: NO AUTORIZADO');
                _showCanvasError('admin-chart-regs', '> ERROR DE TELEMETRÍA: NO AUTORIZADO');
                _showCanvasError('admin-chart-plants', '> ERROR DE TELEMETRÍA: NO AUTORIZADO');
            } else {
                _showCanvasError('admin-chart-users', '> SIN CONEXIÓN CON EL CLÚSTER');
                _showCanvasError('admin-chart-regs', '> SIN CONEXIÓN CON EL CLÚSTER');
                _showCanvasError('admin-chart-plants', '> SIN CONEXIÓN CON EL CLÚSTER');
            }
        });
}

function _renderAdminCharts(data) {
    if(adminChart1) adminChart1.destroy();
    if(adminChart2) adminChart2.destroy();
    if(adminChart3) adminChart3.destroy();

    const chartStyle = { color: '#00e5ff', font: { family: 'Share Tech Mono' } };

    const ctx1 = document.getElementById('admin-chart-users').getContext('2d');
    adminChart1 = new Chart(ctx1, {
        type: 'doughnut',
        data: { labels: ['Activos', 'Inactivos', 'Suspendidos'], datasets: [{ data: data.users || [0,0,0], backgroundColor: ['#00e5ff', '#005577', '#ff4444'], borderColor: '#000511', borderWidth: 2 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: chartStyle } } }
    });

    const ctx2 = document.getElementById('admin-chart-regs').getContext('2d');
    adminChart2 = new Chart(ctx2, {
        type: 'line',
        data: { labels: ['LUN','MAR','MIE','JUE','VIE','SAB','DOM'], datasets: [{ label: 'Nuevos Operadores', data: data.regs || [0,0,0,0,0,0,0], borderColor: '#00e5ff', backgroundColor: 'rgba(0, 229, 255, 0.2)', fill: true, tension: 0.3 }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: chartStyle, grid: { color: 'rgba(0,229,255,0.1)' } }, y: { ticks: chartStyle, grid: { color: 'rgba(0,229,255,0.1)' } } }, plugins: { legend: { display: false } } }
    });

    const ctx3 = document.getElementById('admin-chart-plants').getContext('2d');
    
    // Configuración Monitor Vital (Tiempo Real) - initialize with zeros and only update from server
    const initialTimeLabels = Array.from({length: 20}, () => '');

    adminChart3 = new Chart(ctx3, {
        type: 'line',
        data: {
            labels: initialTimeLabels,
            datasets: [
                { label: 'Humedad (%)', data: Array(20).fill(0), borderColor: '#00ffaa', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.3 },
                { label: 'Temp (C)', data: Array(20).fill(0), borderColor: '#ff4444', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.3 },
                { label: 'pH (x10)', data: Array(20).fill(0), borderColor: '#eab308', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.3 },
                { label: 'UV (x10)', data: Array(20).fill(0), borderColor: '#00e5ff', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.3 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            scales: {
                x: { display: false },
                y: { grid: { color: 'rgba(0,229,255,0.1)' }, ticks: chartStyle, min: 0, max: 100 }
            },
            plugins: {
                legend: { display: true, labels: { color: '#00e5ff', font: { family: 'Share Tech Mono', size: 10 } } }
            }
        }
    });

    if (!window.telemetryIntervalId) {
        window.telemetryIntervalId = setInterval(actualizarTelemetriaGlobal, 4000);
    }
}

// Fetch admin stats and render charts. Returns a promise resolving with the data object.
async function fetchAdminStats() {
    // Redundant guard: only run when admin feed is present and token exists.
    const adminFeed = document.getElementById('live-notifications-feed');
    if (!adminFeed) return Promise.resolve({});
    if (!window.moleApi || !window.moleApi.isTokenPresent() || window.moleApi.isTokenExpired()) {
        // Silent exit to avoid polluting console when user is not admin or token missing
        return Promise.resolve({});
    }
    try {
        const data = await window.moleApi.get('admin/stats/', { silent: true });
        _renderAdminCharts(data || {});
        return data || {};
    } catch (err) {
        // bubble up the error so callers (init) can display appropriate overlays
        throw err;
    }
}

async function actualizarTelemetriaGlobal() {
    if (!adminChart3 || adminChart3.config.type !== 'line') return;
    try {
        let newData = [];
        if (window.moleApi && window.moleApi.isTokenPresent()) {
            const resp = await window.moleApi.get('admin/stats/', { silent: true });
            newData = resp.health || [];
        }
        const baseH = typeof newData[0] === 'number' ? newData[0] : 0;
        const baseT = typeof newData[1] === 'number' ? newData[1] : 0;
        const baseUv = typeof newData[3] === 'number' ? newData[3] : 0;
        const basePh = typeof newData[4] === 'number' ? newData[4] : 0;

        adminChart3.data.datasets[0].data.shift();
        adminChart3.data.datasets[0].data.push(baseH);

        adminChart3.data.datasets[1].data.shift();
        adminChart3.data.datasets[1].data.push(baseT);

        adminChart3.data.datasets[2].data.shift();
        adminChart3.data.datasets[2].data.push(basePh * 10);

        adminChart3.data.datasets[3].data.shift();
        adminChart3.data.datasets[3].data.push(baseUv * 10);

        adminChart3.update();
    } catch(err) {}
}

function agregarNotificacion(mensaje, tipo = 'info') {
    const feed = document.getElementById('live-notifications-feed');
    if (!feed) return;
    const div = document.createElement('div');
    const time = new Date().toLocaleTimeString('en-GB');
    let color = 'text-[#00ffaa]'; let tag = '[INFO]';
    if (tipo === 'warn') { color = 'text-[#eab308]'; tag = '[WARN]'; }
    if (tipo === 'error') { color = 'text-[#ff4444] animate-pulse'; tag = '[CRIT]'; }
    div.className = `border-b border-white/5 pb-1 mb-1 ${color}`;
    div.innerText = `[${time}] ${tag} ${mensaje}`;
    feed.appendChild(div);
    feed.scrollTop = feed.scrollHeight;
}

function pollLiveAlerts() {
    // Redundant guard: ensure this only runs when admin feed exists and token present.
    const adminFeed = document.getElementById('live-notifications-feed');
    if (!adminFeed) return;
    if (!window.moleApi || !window.moleApi.isTokenPresent() || window.moleApi.isTokenExpired()) return;

    // GATING POR ROL ESTRUCTURAL
    let isAdmin = false;
    try {
        const r = localStorage.getItem('moleia_role');
        isAdmin = (r === 'admin' || r === 'superuser');
    } catch(e) {}
    if (!isAdmin) return;

    if (window.notificationsIntervalId) return;

    window.notificationsIntervalId = setInterval(async () => {
        // If the feed was removed from DOM (navigated away), clear the interval.
        const feedEl = document.getElementById('live-notifications-feed');
        if (!feedEl) {
            try { clearInterval(window.notificationsIntervalId); } catch(e) {}
            window.notificationsIntervalId = null;
            return;
        }

        if (!window.moleApi || !window.moleApi.isTokenPresent() || window.moleApi.isTokenExpired()) return;
        try {
            const data = await window.moleApi.get('admin/telemetry/latest/', { silent: true });
            const feed = document.getElementById('live-notifications-feed');
            // Si la llamada fue exitosa y trajo alertas, limpiamos y actualizamos
            if (feed) feed.innerHTML = '';
            if (data && data.alerts && data.alerts.length > 0) {
                data.alerts.forEach(evt => agregarNotificacion(evt.msg, evt.tipo));
            }
        } catch(err) {
            // Silent on token/authorization issues to avoid spamming console in non-admin views
        }
    }, 8000);
}

// polling start is now scoped to admin views (triggered on DOMContentLoaded when appropriate)

function downloadAdminReport() {
    const users = JSON.parse(localStorage.getItem('moleia_users'));
    const totalUsers = Object.keys(users).length;
    const date = new Date().toLocaleString();
    const fileContent = '\n====================================================\n      REPORTE DEL SISTEMA MOLE-IA - MODO ADMIN\n====================================================\nFECHA DE EXTRACCIÓN: ' + date + '\nSUPERVISOR A CARGO: ADMIN\n\n--- ESTADÍSTICAS GLOBALES ---\nTOTAL DE USUARIOS REGISTRADOS: ' + totalUsers + '\nESTADO DEL SERVIDOR: ONLINE\nNIVEL DE RADIACIÓN EXTERNA: ESTABLE\n\n--- RESUMEN DE CULTIVOS ---\n- MANZANILLA: Crecimiento óptimo (Sector A)\n- PEYOTE: Cuarentena preventiva (Sector B)\n- HONGOS: Producción al 90% (Sector Subterráneo)\n\n[FIN DEL REPORTE]\n====================================================\n    ';
    const blob = new Blob([fileContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'MOLE-IA_REPORTE_' + Date.now() + '.txt';
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); window.URL.revokeObjectURL(url);
}

function renderLogList() {
    const logContainer = document.getElementById('log-list');
    if(!logContainer) return;
    const logs = [
        { time: '12:45:22', event: 'SISTEMA', detail: 'Calibración biométrica finalizada', status: '[OK]' },
        { time: '11:30:10', event: 'ALERTA', detail: 'Humedad crítica detectada', status: '[WARN]' },
        { time: '10:00:00', event: 'RIEGO', detail: 'Activación de micro-goteo', status: '[ACTIVE]' },
    ];
    let logHTML = '<div class="grid grid-cols-12 gap-4 text-[#00ffaa]/50 border-b border-[#00ffaa]/30 pb-2 mb-3 tracking-widest text-xs"><div class="col-span-2 font-bold">HORA</div><div class="col-span-2 font-bold">EVENTO</div><div class="col-span-6 font-bold">DETALLE</div><div class="col-span-2 font-bold text-center">ESTADO</div></div>';
    logHTML += logs.map(log => {
        let statusClass = 'text-[#00ffaa]';
        if(log.status === '[WARN]') statusClass = 'text-red-500 animate-pulse font-bold';
        if(log.status === '[ACTIVE]') statusClass = 'text-[#f97316]';
        return '<div class="grid grid-cols-12 gap-4 border-b border-[#00ffaa]/10 py-3 hover:bg-[#00ffaa]/5 transition-colors"><div class="col-span-2 text-white font-bold opacity-80">' + log.time + '</div><div class="col-span-2 text-white font-bold opacity-80">' + log.event + '</div><div class="col-span-6 text-[#00ffaa] opacity-90">' + log.detail + '</div><div class="col-span-2 text-center ' + statusClass + '">' + log.status + '</div></div>';
    }).join('');
    logContainer.innerHTML = logHTML;
}

function openModal() {
    document.getElementById('main-dashboard').classList.add('hidden');
    document.getElementById('analysis-modal').classList.remove('hidden');
    document.getElementById('analysis-modal').classList.add('flex');
    const ctxH = document.getElementById('chart-hum').getContext('2d');
    const ctxT = document.getElementById('chart-temp').getContext('2d');
    
    const getChartOptions = (color, labelText) => ({
        responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
        plugins: { legend: { display: false }, tooltip: { backgroundColor: 'rgba(0, 0, 0, 0.85)', titleColor: color, bodyColor: '#ffffff', titleFont: { family: 'Share Tech Mono', size: 14, weight: 'bold' }, bodyFont: { family: 'Share Tech Mono', size: 14 }, borderColor: color, borderWidth: 1.5, cornerRadius: 0, displayColors: false, padding: 10, caretSize: 6, callbacks: { label: function(context) { return labelText + ': ' + context.parsed.y; } } } },
        scales: { x: { grid: { color: color === '#00ffaa' ? 'rgba(0, 255, 170, 0.1)' : 'rgba(249, 115, 22, 0.1)' }, ticks: { color: color, font: { family: 'Share Tech Mono' } } }, y: { grid: { color: color === '#00ffaa' ? 'rgba(0, 255, 170, 0.1)' : 'rgba(249, 115, 22, 0.1)' }, ticks: { color: color, font: { family: 'Share Tech Mono' } } } }
    });

    if (hChart) hChart.destroy(); if (tChart) tChart.destroy();
    hChart = new Chart(ctxH, { type: 'line', data: { labels: ['00:00','04:00','08:00','12:00','16:00','20:00','24:00'], datasets: [{ data: [65,68,75,60,55,62,65], borderColor: '#00ffaa', backgroundColor: 'rgba(0, 255, 170, 0.1)', fill: true, tension: 0.4, pointRadius: 5, pointHoverRadius: 8, pointBackgroundColor: '#000000', pointBorderColor: '#00ffaa', pointBorderWidth: 2 }] }, options: getChartOptions('#00ffaa', 'Humedad') });
    tChart = new Chart(ctxT, { type: 'line', data: { labels: ['00:00','04:00','08:00','12:00','16:00','20:00','24:00'], datasets: [{ data: [22,20,24,28,27,24,23], borderColor: '#f97316', stepped: true, pointRadius: 5, pointHoverRadius: 8, pointBackgroundColor: '#000000', pointBorderColor: '#f97316', pointBorderWidth: 2 }] }, options: getChartOptions('#f97316', 'Temperatura') });
    renderLogList();
}

function closeModal() {
    document.getElementById('analysis-modal').classList.add('hidden');
    document.getElementById('analysis-modal').classList.remove('flex');
    document.getElementById('main-dashboard').classList.remove('hidden');
}

setInterval(() => { const c = document.getElementById('clock'); if(c) c.innerText = new Date().toLocaleTimeString('en-GB'); }, 1000);

// ==========================================================
// 5. SISTEMAS DE SUPERVISOR (OVERRIDE Y ESCÁNER)
// ==========================================================

// initPlantsDB and local mock overrides removed. Production uses backend-owned plants.
function triggerOverride(type) {
    // Administrative override is disabled for production-backed mode.
    // For safety, we notify operator and do not mutate client-side mocks.
    if (type === 'sequia') {
        alert('OVERRIDE DESHABILITADO: Las acciones de manipulación de datos locales están deshabilitadas en modo integrado.');
    } else if (type === 'fallo_riego') {
        alert('OVERRIDE DESHABILITADO: Las acciones de manipulación de datos locales están deshabilitadas en modo integrado.');
    } else if (type === 'restaurar') {
        alert('OVERRIDE DESHABILITADO: Restauración local no disponible.');
    }
}

async function runDiagnostic() {
    const term = document.getElementById('diagnostic-term');
    term.innerHTML = '';
    const lines = ["> INICIANDO PROTOCOLO DE DIAGNÓSTICO...", "> ESTABLECIENDO CONEXIÓN CON SENSORES...", "----------------------------------------"];

    if (!window.moleApi || !window.moleApi.isTokenPresent()) {
        term.innerHTML = lines.join('\n') + '\n> ERROR: No autenticado. Inicia sesión para ejecutar diagnóstico.';
        return;
    }

    try {
        const plants = await window.moleApi.get('plants/my-collection/', { silent: true });
        const targets = plants.slice(0, 4);
        for (const p of targets) {
            const telemetry = await (async () => {
                try {
                    return await window.moleApi.get('telemetry/latest/?plant_id=' + p.id, { silent: true });
                } catch (e) { return null; }
            })();

            const humedad = telemetry && telemetry.soil_humidity !== undefined ? (Math.round(telemetry.soil_humidity) + '%') : 'N/D';
            const temp = telemetry && telemetry.air_temperature !== undefined ? (Math.round(telemetry.air_temperature) + '°C') : 'N/D';
            const estado = (telemetry && telemetry.soil_humidity !== undefined && telemetry.soil_humidity < 20) ? "<span class='text-red-500 animate-pulse'>CRÍTICO</span>" : "<span class='text-[#00ffaa]'>ÓPTIMO</span>";
            lines.push('> [' + (p.nickname || 'PLANTA').toUpperCase() + '] Estado: ' + estado);
            lines.push('  | Humedad: ' + humedad + ' | Temp: ' + temp + ' | Integ: ' + (estado.includes('CRÍTICO') ? 'PELIGRO' : 'ESTABLE'));
        }

        term.innerHTML = lines.join('\n');
    } catch (err) {
        console.warn('> runDiagnostic error:', err && err.message);
        term.innerHTML = lines.join('\n') + '\n> ERROR: Falló protocolo de diagnóstico.';
    }
}

// ==========================================================
// 6. SISTEMA DE REPORTES Y BANDEJA DE ADMIN
// ==========================================================

function openContactModal() {
    document.getElementById('contact-modal').classList.remove('hidden');
    const loginInput = document.getElementById('user-input');
    const userField = document.getElementById('contact-user');
    if (loginInput && loginInput.value.trim() !== '') { userField.value = loginInput.value.toUpperCase(); }
    else { userField.value = "OPERADOR_DESCONOCIDO"; }
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
        btnStatus.classList.remove('hidden'); return;
    }
    btnStatus.innerText = "> ENCRIPTANDO Y ENVIANDO DATOS...";
    btnStatus.className = "text-center mt-4 text-xs font-bold text-[#f97316] animate-pulse tracking-widest";
    btnStatus.classList.remove('hidden');
    
    const user = document.getElementById('contact-user').value;
    const type = document.getElementById('contact-type').value;

    if (window.moleApi) {
        window.moleApi.post('reports/intercepted/', { username: user, classification: type, message: msg })
            .then(() => {
                btnStatus.innerText = "TRANSMISIÓN EXITOSA. CENTRAL NOTIFICADA.";
                btnStatus.className = "text-center mt-4 text-xs font-bold text-[#00ffaa] tracking-widest";
                msgInput.value = '';
                setTimeout(() => { closeContactModal(); }, 2000);
                renderAdminReports();
            })
            .catch(err => {
                btnStatus.innerText = "ERROR DE TRANSMISIÓN: " + err.message;
                btnStatus.className = "text-center mt-4 text-xs font-bold text-red-500 animate-pulse tracking-widest";
            });
    } else {
        setTimeout(() => {
            const timestamp = new Date().toLocaleTimeString('en-GB');
            systemReports.push({ time: timestamp, user: user, type: type, message: msg });
            renderAdminReports();
            btnStatus.innerText = "TRANSMISIÓN EXITOSA. CENTRAL NOTIFICADA.";
            btnStatus.className = "text-center mt-4 text-xs font-bold text-[#00ffaa] tracking-widest";
            msgInput.value = '';
            setTimeout(() => { closeContactModal(); }, 2000);
        }, 1500);
    }
}

function renderAdminReports() {
    const container = document.getElementById('admin-reports-list');
    if(!container) return;
    container.innerHTML = '<div class="text-center text-[#00e5ff] opacity-50 text-xs py-8 animate-pulse">> OBTENIENDO REPORTES INTERCEPTADOS...</div>';

    // Zero-Trust: require valid JWT to fetch admin reports
    if (!window.moleApi || !window.moleApi.isTokenPresent() || window.moleApi.isTokenExpired()) {
        _showContainerError('admin-reports-list', '> ERROR DE TELEMETRÍA: NO AUTORIZADO');
        return;
    }

    window.moleApi.get('reports/intercepted/')
        .then(data => {
            const reports = Array.isArray(data) ? data : (data.reports || []);
            if(reports.length === 0) {
                container.innerHTML = '<div class="text-center opacity-50 text-xs py-8">> NO HAY REPORTES EN LA BANDEJA...</div>'; 
                return;
            }
            container.innerHTML = reports.map(rep => '<div class="grid grid-cols-12 gap-4 text-xs border-b border-[#00e5ff]/10 py-3 px-2 hover:bg-[#00e5ff]/10 transition-colors"><div class="col-span-2 text-[#00e5ff]/70 font-bold">' + sanitizeHTML(rep.time || new Date(rep.created_at || Date.now()).toLocaleTimeString('en-GB')) + '</div><div class="col-span-3 text-white">' + sanitizeHTML(rep.user || rep.username || '--') + '</div><div class="col-span-3 text-[#f97316] uppercase font-bold">' + sanitizeHTML((rep.type||rep.classification||'GENERAL').replace(/_/g, ' ')) + '</div><div class="col-span-4 opacity-80 break-words">' + sanitizeHTML(rep.message) + '</div></div>').join('');
        })
        .catch(err => {
            console.warn('> Error fetch intercepted reports:', err);
            if (err && (err.status === 401 || err.status === 403)) {
                _showContainerError('admin-reports-list', '> ERROR DE TELEMETRÍA: NO AUTORIZADO');
            } else {
                _showContainerError('admin-reports-list', '> SIN CONEXIÓN CON EL CLÚSTER');
            }
        });
}

function generateMasterReport() {
    const btn = document.querySelector('button[onclick="generateMasterReport()"]');
    if (btn) {
        btn.innerText = "[ ENVIANDO A MS3... ]";
        btn.classList.add('animate-pulse');
        btn.disabled = true;
    }

    if (!window.moleApi) {
        if(btn) { btn.innerText = "[ EXPORTAR REPORTE MAESTRO ]"; btn.classList.remove('animate-pulse'); btn.disabled = false; }
        if(window.ApiService) window.ApiService.showToast("API no disponible para MLOps.", "error"); 
        return; 
    }

    if(window.ApiService) window.ApiService.showToast("Invocando MS3 Celery...", "info");

    window.moleApi.post('reports/master/', {})
        .then(data => {
            const jobId = data.job_id || data.id || data.task_id;
            if (!jobId) throw new Error("No Job ID returned from MS3.");
            if (btn) btn.innerText = "[ COMPILANDO PDF... ]";
            return _pollMasterReport(jobId, btn);
        })
        .catch(err => {
            console.error("> MS3 Master Report Error:", err);
            if(window.ApiService) window.ApiService.showToast("Fallo al generar reporte: " + err.message, "error");
            if (btn) {
                btn.innerText = "[ EXPORTAR REPORTE MAESTRO ]";
                btn.classList.remove('animate-pulse');
                btn.disabled = false;
            }
        });
}

function _pollMasterReport(jobId, btn) {
    const maxAttempts = 20;
    let attempts = 0;
    
    const interval = setInterval(() => {
        attempts++;
        window.moleApi.get(`reports/master/status/${jobId}/`)
            .then(res => {
                if (res.status === 'completed' || res.state === 'SUCCESS') {
                    clearInterval(interval);
                    if(window.ApiService) window.ApiService.showToast("Reporte completado. Descargando...", "success");
                    if (btn) { btn.innerText = "[ EXPORTAR REPORTE MAESTRO ]"; btn.classList.remove('animate-pulse'); btn.disabled = false; }
                    
                    const fileUrl = res.file_url || res.url || res.pdf_url || res.result;
                    if (fileUrl) {
                        const a = document.createElement('a');
                        a.href = fileUrl; a.download = 'MOLE_IA_REPORTE.pdf'; a.target = '_blank';
                        document.body.appendChild(a); a.click(); document.body.removeChild(a);
                    }
                } else if (res.status === 'failed' || res.state === 'FAILURE') {
                    clearInterval(interval);
                    throw new Error("El modelo MS3 falló en la generación.");
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    throw new Error("Tiempo de espera agotado.");
                }
            })
            .catch(err => {
                if(err.status === 404 && attempts < maxAttempts) {
                   // Aún no encuentra el task, we can keep trying or abort. Let's keep trying if standard generic 404, or abort right away if backend is fully rigid:
                   return; // ignore 404 on polling as it might not be ready in some async systems
                }
                clearInterval(interval);
                if(window.ApiService) window.ApiService.showToast("Error consultando MS3: " + err.message, "error");
                if (btn) { btn.innerText = "[ EXPORTAR REPORTE MAESTRO ]"; btn.classList.remove('animate-pulse'); btn.disabled = false; }
            });
    }, 2000);
}

function backToIntro() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('intro-screen').classList.remove('hidden');
    document.getElementById('user-input').value = '';
    document.getElementById('pass-input').value = '';
    document.getElementById('login-error').classList.add('hidden');
}

// ==========================================================
// 7. FUNCIONES PARA NUEVOS USUARIOS Y MODAL DE CULTIVOS
// ==========================================================

function setEmptyDashboardState() {
    document.getElementById('txt-hum').innerText = '--%';
    document.getElementById('txt-temp').innerText = '--°C';
    document.getElementById('txt-ph').innerText = '--';
    document.getElementById('txt-uv').innerText = 'N/A';
    const plantTag = document.getElementById('plant-tag');
    plantTag.innerText = 'SIN SEÑAL';
    plantTag.classList.add('text-red-500', 'animate-pulse');
    plantTag.classList.remove('text-[#00ffaa]');
    const mainImgContainer = document.getElementById('main-img');
    const parentContainer = mainImgContainer.parentElement;
    mainImgContainer.style.display = 'none';
    if (!document.getElementById('no-signal-container')) {
        const noSignal = document.createElement('div');
        noSignal.id = 'no-signal-container';
        noSignal.className = "text-[#00ffaa] opacity-50 flex flex-col items-center justify-center w-full h-full min-h-[250px] border border-dashed border-[#00ffaa]/30";
        noSignal.innerHTML = '<svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg><p class="text-xs tracking-widest text-center">> VINCULE UN CULTIVO <br> PARA INICIAR MONITOREO</p>';
        parentContainer.appendChild(noSignal);
    } else { document.getElementById('no-signal-container').style.display = 'flex'; }
}

function openAddPlantModal() { document.getElementById('add-plant-modal').classList.remove('hidden'); }
function closeAddPlantModal() { document.getElementById('add-plant-modal').classList.add('hidden'); }
function registerNewPlant() {
    console.log("> Procesando inicialización de nuevo cultivo...");
    alert("[ OK ] Cultivo inicializado en la base de datos local.");
    closeAddPlantModal();
}

const originalUpdatePlant = updatePlant;
updatePlant = function(name) {
    const mainImg = document.getElementById('main-img');
    const noSignal = document.getElementById('no-signal-container');
    if (mainImg) mainImg.style.display = 'block';
    if (noSignal) noSignal.style.display = 'none';
    originalUpdatePlant(name);
};

// ==========================================================
// 8. FLUJO DE DIAGNÓSTICO (CÁMARA Y DEEPSEEK)
// ==========================================================

async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 1. Mostrar la imagen en la tarjeta de resultados (preview dinámico)
    // Usa URL.createObjectURL para previsualizar directamente desde el blob del usuario
    const previewEl = document.getElementById('scanned-image-preview');
    // Revocar URL anterior para evitar memory leaks
    if (previewEl.src && previewEl.src.startsWith('blob:')) {
        URL.revokeObjectURL(previewEl.src);
    }
    previewEl.src = URL.createObjectURL(file);

    // If session is not ready, abort immediately (hard guard)
    try {
        if (!window.moleApi || !window.moleApi.sessionReady) {
            // Hide loading UI and inform user
            try { document.getElementById('loading-scan-modal').classList.add('hidden'); } catch (e) {}
            try { document.getElementById('diagnosis-result-modal').classList.remove('hidden'); } catch (e) {}
            try { document.getElementById('diag-treatment').className = 'text-red-500'; document.getElementById('diag-treatment').innerText = 'Sesión no iniciada. Inicia sesión para usar esta función.'; } catch (e) {}
            try { if (window.ApiService && typeof window.ApiService.showToast === 'function') window.ApiService.showToast('Función restringida: inicia sesión primero.', 'error'); } catch (e) {}
            return;
        }
    } catch (e) { /* ignore guard failures */ }

    // 2. Mostrar pantalla de carga
    document.getElementById('loading-scan-modal').classList.remove('hidden');

    // 3. Preparar los datos para el POST
    const formData = new FormData();
    formData.append('image', file);

    try {
        let taskResponse;
        if (window.moleApi) {
            try {
                // UI de Tensión Ciberpunk
                document.getElementById('diag-species').innerText = "[ INICIANDO PROTOCOLO DE EXTRACCIÓN ]";
                document.getElementById('diag-status').innerText = "ENVIANDO A RED NEURAL...";
                document.getElementById('diag-ph').innerText = "CALCULANDO...";
                document.getElementById('diag-treatment').className = "text-[#f97316] animate-pulse";
                document.getElementById('diag-treatment').innerText = "_esperando telemetría de procesamiento_";
                
                // Mostrar pantalla de resultado temporalmente mientras se procesa
                document.getElementById('loading-scan-modal').classList.add('hidden');
                document.getElementById('diagnosis-result-modal').classList.remove('hidden');

                taskResponse = await window.moleApi.upload('ai/vision/analyze/', formData);
            } catch (err) {
                console.warn("> Fallo en la red o en el backend, no se puede continuar.");
                throw err;
            }
        } else {
            throw new Error("API service no disponible.");
        }

        // POLLING ASÍNCRONO — maneja status: 'success' | 'failure' | 'pending'
        let data = null;
        if (taskResponse && taskResponse.task_id) {
            const taskId = taskResponse.task_id;
            let attempts = 0;
            while (attempts < 20) { // 40 seconds max timeout
                await new Promise(r => setTimeout(r, 2000));
                const pollRes = await window.moleApi.get(`ai/vision/status/${taskId}/`);

                // ── ÉXITO: resolver la promesa con el resultado ──
                if (pollRes.state === 'SUCCESS' || pollRes.status === 'success') {
                    data = pollRes.result;
                    break;
                }

                // ── FALLO: romper el bucle de inmediato y lanzar excepción ──
                if (pollRes.state === 'FAILURE' || pollRes.status === 'failure') {
                    const serverError = pollRes.error || pollRes.message || 'Error desconocido del motor de IA.';
                    throw new Error(`La red neural reportó un fallo crítico: ${serverError}`);
                }

                attempts++;
            }
            if (!data) throw new Error("Timeout esperando al motor de IA.");
        } else {
            data = taskResponse; // Fallback sync si el backend no respondió con task_id
        }

        // 4. Llenar la tarjeta de diagnóstico con los datos
        document.getElementById('diag-treatment').className = "text-[#00ffaa] flex items-center";
        
        // Mapear resultado del MS1 (DiagnosticModel)
        const illness = (data.illness_name || 'NINGUNA').toUpperCase();
        const conf = data.confidence ? (data.confidence * 100).toFixed(1) + '%' : '--';
        
        document.getElementById('diag-species').innerText = `>> AMENAZA DETECTADA: ${illness} [CONFIANZA: ${conf}]`;
        document.getElementById('diag-status').innerText = `ESPECIE IDENTIFICADA: ${(data.species || '--').toUpperCase()}`;
        document.getElementById('diag-ph').innerText = data.suggested_ph || '--';
        document.getElementById('diag-treatment').innerHTML = `<span class="mr-2">></span> ${sanitizeHTML(data.recommended_treatment || 'MANTENER MONITOREO').toUpperCase()}`;

    } catch (error) {
        console.error("Error en conexión con el motor IA:", error);
        document.getElementById('diag-species').innerText = "ERROR DE CONEXIÓN";
        document.getElementById('diag-status').innerText = "Fallo al contactar servidor.";
        document.getElementById('diag-ph').innerText = "--";
        document.getElementById('diag-treatment').innerText = "Verifique su red. El backend está apagado o inaccesible.";
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
        // SIMULACIÓN DE API: Esperamos 1.5 segundos para fingir que descargamos
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Creamos un Blob falso simulando ser un PDF (Solo para la prueba visual)
        const pdfContent = "%PDF-1.4\\n% Simulación de reporte fitosanitario para MOLE-IA...\\n% Especie sana. Fin del reporte.";
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
        
        console.log("> Datos enviados al endpoint de aprovisionamiento IoT.");
    }, 3000);
}

// Funciones para el Perfil del Operador
function openUserProfile() {
    console.log("> Accediendo a datos del operador...");
    document.getElementById('user-profile-modal').classList.remove('hidden');
}

function closeUserProfile() {
    document.getElementById('user-profile-modal').classList.add('hidden');
}

// Modificación a la función de purga para que cierre el perfil antes de abrir la alerta roja
function openDeleteModal() {
    closeUserProfile(); // Cerramos el perfil para que no se encimen
    if(document.getElementById('delete-account-modal')) {
        document.getElementById('delete-account-modal').classList.remove('hidden');
        if(document.getElementById('confirm-delete-input')) {
            document.getElementById('confirm-delete-input').value = '';
        }
    } else {
        alert("SOLICITUD DE ELIMINACIÓN: Contacte al administrador del sistema.");
    }
}

// Cleanup del token auth global si llegara a existir al reiniciar
window.addEventListener('beforeunload', () => {
    if (window.moleApi) { window.moleApi.clearToken(); }
});

// ==========================================================
// 12. MÓDULOS ADMIN: RBAC, FLORA, MLOPS, IMPERSONACIÓN
// ==========================================================

function openUserCreationModal() {
    document.getElementById('user-creation-modal').classList.remove('hidden');
    document.getElementById('new-user-name').value = '';
    document.getElementById('new-user-pass').value = '';
}

function closeUserCreationModal() {
    document.getElementById('user-creation-modal').classList.add('hidden');
}

function createNewUser() {
    const username = document.getElementById('new-user-name').value;
    const password = document.getElementById('new-user-pass').value;
    const role = document.getElementById('new-user-role').value;
    let perms = document.getElementById('new-user-perms').value;
    
    if(!username || !password) {
        window.ApiService.showToast("Nombre y contraseña son obligatorios.", "error"); return;
    }
    
    let permissions = [];
    if(perms) {
        try { permissions = JSON.parse(perms); } 
        catch(e) { window.ApiService.showToast("El formato de permisos debe ser un JSON Array válido.", "error"); return; }
    }
    
    const btn = document.getElementById('btn-create-usr');
    btn.innerText = "[ PROCESANDO... ]"; btn.classList.add('animate-pulse');
    
    if (window.moleApi) {
        window.moleApi.post('admin/users/', { username, password, role, permissions })
            .then(data => {
                window.ApiService.showToast("Usuario " + username + " creado exitosamente con rol " + role, "success");
                closeUserCreationModal();
            })
            .catch(err => {
                window.ApiService.showToast("Error al crear usuario: " + err.message, "error");
            })
            .finally(() => {
                btn.innerText = "> REGISTRAR CREDENCIALES"; btn.classList.remove('animate-pulse');
            });
    } else {
        window.ApiService.showToast("Modo Offline: Usuario creado localmente.", "success");
        closeUserCreationModal();
        btn.innerText = "> REGISTRAR CREDENCIALES"; btn.classList.remove('animate-pulse');
    }
}

function openAdminAddPlantModal() {
    document.getElementById('admin-add-plant-modal').classList.remove('hidden');
    document.getElementById('admin-plant-name').value = '';
    document.getElementById('admin-plant-file').value = '';
    document.getElementById('admin-plant-img').value = '';
}

function closeAdminAddPlantModal() {
    document.getElementById('admin-add-plant-modal').classList.add('hidden');
}

function adminRegisterNewPlant() {
    const name = document.getElementById('admin-plant-name').value;
    const classification = document.getElementById('admin-plant-class').value;
    const fileInput = document.getElementById('admin-plant-file');
    const imgInput = document.getElementById('admin-plant-img');
    
    if(!name) { window.ApiService.showToast("El nombre del cultivo es obligatorio.", "error"); return; }

    const formData = new FormData();
    formData.append('name', name);
    formData.append('classification', classification);
    if(fileInput.files[0]) formData.append('technical_file', fileInput.files[0]);
    if(imgInput.files[0]) formData.append('image', imgInput.files[0]);

    const btn = document.getElementById('btn-admin-plant');
    btn.innerText = "[ SUBIENDO... ]"; btn.classList.add('animate-pulse');

    if (window.moleApi) {
        window.moleApi.upload('plants/', formData)
            .then(data => {
                window.ApiService.showToast("Cultivo " + name + " registrado en el catálogo central.", "success");
                closeAdminAddPlantModal();
            })
            .catch(err => {
                window.ApiService.showToast("Error al registrar flora: " + err.message, "error");
            })
            .finally(() => {
                btn.innerText = "> GUARDAR E INICIALIZAR"; btn.classList.remove('animate-pulse');
            });
    } else {
        window.ApiService.showToast("Modo Offline: Flora registrada localmente.", "success");
        closeAdminAddPlantModal();
        btn.innerText = "> GUARDAR E INICIALIZAR"; btn.classList.remove('animate-pulse');
    }
}

function switchToOperatorMode() {
    document.getElementById('admin-dashboard').classList.add('hidden');
    document.getElementById('admin-dashboard').classList.remove('flex');
    
    document.getElementById('main-dashboard').classList.remove('hidden');
    document.getElementById('main-dashboard').classList.add('flex');
    
    document.getElementById('return-override-btn').classList.remove('hidden');
    
    // Simulate re-fetching view
    setEmptyDashboardState(); // or load normal UI features
    
    if(window.ApiService) window.ApiService.showToast("Modo Impersonación Activado. Vista de Operador.", "warn");
}

function returnToOverride() {
    document.getElementById('main-dashboard').classList.add('hidden');
    document.getElementById('main-dashboard').classList.remove('flex');
    
    document.getElementById('admin-dashboard').classList.remove('hidden');
    document.getElementById('admin-dashboard').classList.add('flex');
    
    document.getElementById('return-override-btn').classList.add('hidden');
    if(window.ApiService) window.ApiService.showToast("Retorno a Override Central.", "info");
}

function trainRagModel() {
    const fileInput = document.getElementById('mlops-rag-file');
    if(!fileInput.files[0]) { window.ApiService.showToast("Seleccione un PDF o TXT primero.", "error"); return; }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    const btn = document.getElementById('btn-train-rag');
    btn.innerText = "[ ENVIANDO A MS2... ]"; btn.classList.add('animate-pulse');
    
    if (window.moleApi) {
        window.moleApi.upload('ai/train/rag/', formData)
            .then(data => {
                window.ApiService.showToast("RAG Alimentado exitosamente", "success");
                fileInput.value = '';
            })
            .catch(err => window.ApiService.showToast("Error en MS2: " + err.message, "error"))
            .finally(() => { btn.innerText = "[ ALIMENTAR RAG ]"; btn.classList.remove('animate-pulse'); });
    } else {
        setTimeout(() => {
            window.ApiService.showToast("RAG Alimentado (Simulación)", "success");
            btn.innerText = "[ ALIMENTAR RAG ]"; btn.classList.remove('animate-pulse');
            fileInput.value = '';
        }, 1500);
    }
}

function trainCnnModel() {
    const fileInput = document.getElementById('mlops-cnn-file');
    if(!fileInput.files || fileInput.files.length === 0) { window.ApiService.showToast("Seleccione un ZIP o imágenes.", "error"); return; }
    
    const formData = new FormData();
    for(let i=0; i<fileInput.files.length; i++) {
        formData.append('dataset', fileInput.files[i]);
    }
    
    const btn = document.getElementById('btn-train-cnn');
    btn.innerText = "[ INICIANDO FINE-TUNING... ]"; btn.classList.add('animate-pulse');
    
    if (window.moleApi) {
        window.moleApi.upload('ai/train/vision/', formData)
            .then(data => {
                window.ApiService.showToast("Entrenamiento CNN completado", "success");
                fileInput.value = '';
            })
            .catch(err => window.ApiService.showToast("Error en MS1: " + err.message, "error"))
            .finally(() => { btn.innerText = "[ INICIAR FINE-TUNING ]"; btn.classList.remove('animate-pulse'); });
    } else {
        setTimeout(() => {
            window.ApiService.showToast("Entrenamiento superado (Simulación)", "success");
            btn.innerText = "[ INICIAR FINE-TUNING ]"; btn.classList.remove('animate-pulse');
            fileInput.value = '';
        }, 2500);
    }
}
