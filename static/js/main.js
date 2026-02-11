/**
 * MOLE-AI MAIN SCRIPT - PROD v1.1
 * Conexión Real + Nuevos Campos de Registro
 */

// --- 1. INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar Cliente Supabase
    if (window.supabase && window.APP_CONFIG) {
        window.supabaseClient = window.supabase.createClient(
            window.APP_CONFIG.SUPABASE.URL,
            window.APP_CONFIG.SUPABASE.ANON_KEY
        );
        window.apiService = new ApiService(window.APP_CONFIG.API_URL, window.supabaseClient);
    } else {
        console.error("Faltan librerías o configuración.");
    }

    // Cargar fondo del chat
    const chatContainer = document.getElementById('ai-chat-container');
    if(chatContainer) {
        chatContainer.style.backgroundImage = "url('/static/assets/topo.png')";
        chatContainer.style.backgroundSize = "150px";
        chatContainer.style.opacity = "1";
    }
    console.log("Mole-IA System Online.");
});

// --- 2. INTRODUCCIÓN (Visual) ---
let typingTimer; 
const speed = 15; 
const introData = {
    giro: "OBJETIVO:<br>Desarrollar soluciones tecnológicas.<br><br>GIRO:<br>Agro-tecnología.",
    vision: "VISIÓN:<br>Sabiduría ancestral + Inteligencia Artificial.",
    flora: "FLORA MEXICANA:<br>Catalogar, monitorear y enseñar.",
    web: "ACERCA DE:<br>Mole-IA Protocol v1.0.<br>Sistema conectado y operativo."
};

function updateIntro(key) {
    const display = document.getElementById('intro-text');
    const fullText = introData[key];
    if(!fullText) return;
    display.innerHTML = "> "; 
    if (typingTimer) clearInterval(typingTimer);
    let i = 0;
    typingTimer = setInterval(() => {
        const char = fullText.charAt(i);
        if (char === '<') {
            const tagEnd = fullText.indexOf('>', i);
            display.innerHTML += fullText.substring(i, tagEnd + 1);
            i = tagEnd + 1;
        } else { display.innerHTML += char; i++; }
        if (i >= fullText.length) { clearInterval(typingTimer); display.innerHTML += '<span class="cursor-blink">_</span>'; }
    }, speed);
}

function irALogin() {
    document.getElementById('start-screen').classList.remove('active');
    document.getElementById('login-screen').classList.add('active');
}

// --- 3. AUTENTICACIÓN Y REGISTRO ---

async function entrarSistema() {
    const email = document.getElementById('email-input').value.trim();
    const password = document.getElementById('password-input').value.trim();
    
    if (!email || !password) { mostrarError('Credenciales requeridas'); return; }
    
    try {
        setLoadingButton('.login-btn', 'CONECTANDO...');
        const { data, error } = await window.supabaseClient.auth.signInWithPassword({ email, password });
        if (error) throw error;
        
        document.getElementById('login-screen').classList.remove('active');
        document.getElementById('app-screen').classList.add('active');
        iniciarMonitoreoReal(); 
    } catch (err) {
        mostrarError('Error de conexión o credenciales');
    } finally { resetButton('.login-btn', 'ENTRAR >>'); }
}

async function registrarUsuario() {
    // Captura de todos los campos
    const email = document.getElementById('email-input').value.trim();
    const password = document.getElementById('password-input').value.trim();
    const username = document.getElementById('username-input').value.trim();
    const dob = document.getElementById('dob-input').value;

    // Validación extendida
    if (!email || !password || !username || !dob) { 
        mostrarError('Todos los campos son obligatorios'); return; 
    }
    if (password.length < 6) { 
        mostrarError('La clave debe tener 6 caracteres mín.'); return; 
    }

    try {
        setLoadingButton('.login-btn', 'REGISTRANDO...');
        
        // Envío a Supabase con Metadatos
        const { data, error } = await window.supabaseClient.auth.signUp({
            email: email, 
            password: password,
            options: {
                data: {
                    username: username,
                    birth_date: dob
                }
            }
        });
        
        if (error) throw error;
        
        mostrarExito(':: REGISTRO ENVIADO. REVISA TU EMAIL ::');
        setTimeout(volverALogin, 4000); // Volver al login automáticamente
    } catch (err) { 
        let msg = err.message;
        if (msg.includes('already registered')) msg = 'El usuario/email ya existe.';
        mostrarError(msg); 
    } finally { 
        resetButton('.login-btn', 'CONFIRMAR >>'); 
    }
}

// --- MÉTODOS DE UI (Cambiar entre Login y Registro) ---

function mostrarRegistro() {
    document.querySelector('.login-title').textContent = 'NUEVO REGISTRO';
    
    // Mostrar campos ocultos
    document.getElementById('register-fields').style.display = 'block';
    
    // Configurar botón principal
    const loginBtn = document.querySelector('.login-btn');
    loginBtn.textContent = 'CONFIRMAR >>';
    loginBtn.setAttribute('onclick', 'registrarUsuario()');
    
    // Configurar enlace de cancelar
    const linkText = document.getElementById('reg-link-text');
    linkText.textContent = "[ Cancelar / Volver ]";
    linkText.setAttribute('onclick', 'volverALogin()');
    linkText.style.textDecoration = "none";
    
    limpiarFormulario();
}

function volverALogin() {
    document.querySelector('.login-title').textContent = 'ACCESO SEGURO';
    
    // Ocultar campos extra
    document.getElementById('register-fields').style.display = 'none';
    
    // Restaurar botón principal
    const loginBtn = document.querySelector('.login-btn');
    loginBtn.textContent = 'ENTRAR >>';
    loginBtn.setAttribute('onclick', 'entrarSistema()');
    
    // Restaurar enlace de registro
    const linkText = document.getElementById('reg-link-text');
    linkText.textContent = "Registrarse";
    linkText.setAttribute('onclick', 'mostrarRegistro()');
    linkText.style.textDecoration = "underline";
    
    limpiarFormulario();
}

// --- 4. LÓGICA DE NEGOCIO (IoT + IA) ---
let plantaActual = 'manzanilla';
let monitorInterval;

function iniciarMonitoreoReal() {
    fetchSensorData();
    monitorInterval = setInterval(fetchSensorData, 5000);
}

async function fetchSensorData() {
    try {
        const data = await window.apiService.get(`sensor-data/latest/?plant=${plantaActual}`);
        if (data) actualizarUI(data);
        else marcarSinDatos();
    } catch (error) { marcarSinDatos(); }
}

function actualizarUI(data) {
    // Campos existentes
    document.getElementById('disp-hum').innerText = (data.soil_humidity || "--") + "%";
    document.getElementById('disp-ph').innerText = (data.ph_level || "--");
    
    // NUEVOS CAMPOS - Temperatura y UV
    document.getElementById('disp-temp').innerText = (data.temperature || "--") + "°C";
    document.getElementById('disp-uv').innerText = (data.uv_index || "--");
    
    // Estado general
    document.getElementById('disp-health').innerText = data.status || "OK";
    const box = document.getElementById('health-box');
    box.className = (data.status === 'DANGER') ? "stat-block danger" : "stat-block";
}

function marcarSinDatos() {
    // Campos existentes
    document.getElementById('disp-hum').innerText = "SIN DATOS";
    document.getElementById('disp-ph').innerText = "SIN DATOS";
    
    // NUEVOS CAMPOS - Temperatura y UV
    document.getElementById('disp-temp').innerText = "SIN DATOS";
    document.getElementById('disp-uv').innerText = "SIN DATOS";
    
    // Estado general
    document.getElementById('disp-health').innerText = "OFFLINE";
    document.getElementById('health-box').className = "stat-block warning";
}

function cambiarPlanta(key, btn) {
    plantaActual = key;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.plant-icon').forEach(i => i.classList.remove('active'));
    const icon = document.getElementById('icon-' + key);
    if(icon) icon.classList.add('active');
    
    document.getElementById('disp-hum').innerText = "CARGANDO...";
    fetchSensorData();
}

// --- 5. CHAT IA ---
function abrirChat() { document.getElementById('ai-modal').style.display = 'flex'; document.getElementById('ai-input').focus(); }
function cerrarChat() { document.getElementById('ai-modal').style.display = 'none'; }

async function enviarComandoAI() {
    const input = document.getElementById('ai-input');
    const chatContainer = document.getElementById('ai-chat-container');
    const question = input.value.trim();
    if(!question) return;

    // Mensaje del usuario
    chatContainer.innerHTML += `<div class="ai-message user">${input.value}</div>`;
    input.value = "";
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Inicializar WebSocket si no está conectado
    if (!window.apiService.isWebSocketConnected()) {
        window.apiService.initWebSocket();
    }
    
    // Escuchar eventos de WebSocket
    window.addEventListener('chatMessage', handleChatResponse);
    
    // Enviar mensaje por WebSocket
    window.apiService.sendChatMessage(question, plantaActual);
}

function handleChatResponse(event) {
    const data = event.detail;
    const chatContainer = document.getElementById('ai-chat-container');
    
    switch(data.type) {
        case 'connection':
        case 'status':
            // Mensajes de estado o conexión
            const statusId = 'status-' + Date.now();
            chatContainer.innerHTML += `<div id="${statusId}" class="ai-message bot status">${data.message}</div>`;
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            // Auto-eliminar mensajes de estado después de 3 segundos
            setTimeout(() => {
                const statusEl = document.getElementById(statusId);
                if (statusEl) statusEl.remove();
            }, 3000);
            break;
            
        case 'response':
            // Eliminar mensajes de estado si existen
            const statusMessages = chatContainer.querySelectorAll('.status');
            statusMessages.forEach(el => el.remove());
            
            // Formatear respuesta con alertas tácticas
            let formattedAnswer = data.answer.replace(/\n/g, '<br>');
            
            // Agregar indicador de alertas tácticas
            if (data.tactical_alerts_count > 0) {
                const alertBadge = `<div class="tactical-alert-indicator">⚠️ ${data.tactical_alerts_count} alertas tácticas</div>`;
                formattedAnswer = alertBadge + formattedAnswer;
            }
            
            // Agregar metadatos de AI
            const metadata = `<div class="ai-metadata">
                🤖 Mole-AI • ${data.processing_time_ms}ms • ${data.model_used}
                ${data.tokens_generated ? `• ${data.tokens_generated} tokens` : ''}
            </div>`;
            
            const responseHtml = `
                <div class="ai-message bot">
                    ${formattedAnswer}
                    ${metadata}
                </div>
            `;
            
            chatContainer.innerHTML += responseHtml;
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            // Destacar alertas tácticas en el texto
            setTimeout(() => {
                const tacticalAlerts = chatContainer.querySelectorAll('.ai-message');
                tacticalAlerts.forEach(el => {
                    if (el.innerHTML.includes('⚠️ ALERTA TÁCTICA')) {
                        el.classList.add('tactical-alert');
                    }
                });
            }, 100);
            break;
            
        case 'error':
            // Eliminar mensajes de estado
            const statusErrors = chatContainer.querySelectorAll('.status');
            statusErrors.forEach(el => el.remove());
            
            chatContainer.innerHTML += `
                <div class="ai-message bot error">
                    ❌ ${data.message}
                </div>
            `;
            chatContainer.scrollTop = chatContainer.scrollHeight;
            break;
            
        default:
            console.log('Tipo de mensaje no manejado:', data.type);
    }
}

// --- 6. HELPERS ---
function mostrarError(msg) {
    const errorDiv = document.getElementById('login-error');
    errorDiv.textContent = msg; errorDiv.style.display = 'block'; errorDiv.style.color = '#ff4444';
}
function mostrarExito(msg) {
    const errorDiv = document.getElementById('login-error');
    errorDiv.textContent = msg; errorDiv.style.display = 'block'; errorDiv.style.color = '#44ff44';
}
function limpiarFormulario() {
    document.getElementById('email-input').value = '';
    document.getElementById('password-input').value = '';
    document.getElementById('username-input').value = '';
    document.getElementById('dob-input').value = '';
    document.getElementById('login-error').style.display = 'none';
}
function setLoadingButton(sel, txt) {
    const btn = document.querySelector(sel);
    btn.dataset.og = btn.textContent; btn.textContent = txt; btn.disabled = true;
}
function resetButton(sel, txt) {
    const btn = document.querySelector(sel);
    btn.textContent = txt || btn.dataset.og; btn.disabled = false;
}
function toggleSys(el) {
    const span = el.querySelector('.stat-value');
    span.innerText = (span.innerText === "OFF") ? "ON" : "OFF";
    el.classList.toggle('active-sys');
}