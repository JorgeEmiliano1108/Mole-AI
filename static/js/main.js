/**
 * MOLE-AI MAIN SCRIPT - PROD v1.1
 * Conexión Real + Nuevos Campos de Registro
 */

// --- 1. INICIALIZACIÓN ---
let pendingImageBase64 = null;
let pendingImageLat = null;
let pendingImageLon = null;

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
    if (chatContainer) {
        chatContainer.style.backgroundImage = "url('/static/assets/topo.png')";
        chatContainer.style.backgroundSize = "150px";
        chatContainer.style.opacity = "1";
    }

    // Listener para captura de imagen (cámara/archivo)
    const cameraInput = document.getElementById('camera-input');
    if (cameraInput) {
        cameraInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (!file) return;
            // Validar tamaño (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                alert('Imagen muy grande. Máximo 5MB.');
                cameraInput.value = '';
                return;
            }
            const reader = new FileReader();
            reader.onload = function (ev) {
                pendingImageBase64 = ev.target.result; // data:image/...;base64,...
                    // Intentar capturar geolocalización al elegir la imagen
                    if (navigator && navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(function(pos) {
                            pendingImageLat = pos.coords.latitude;
                            pendingImageLon = pos.coords.longitude;
                            console.log('Geo captured:', pendingImageLat, pendingImageLon);
                        }, function(err) {
                            console.warn('Geo denied or failed:', err.message);
                            pendingImageLat = null; pendingImageLon = null;
                        }, { enableHighAccuracy: true, timeout: 8000 });
                    }
                // Mostrar preview
                const previewContainer = document.getElementById('image-preview-container');
                const previewThumb = document.getElementById('image-preview-thumb');
                if (previewContainer && previewThumb) {
                    previewThumb.src = pendingImageBase64;
                    previewContainer.style.display = 'flex';
                }
            };
            reader.readAsDataURL(file);
        });
    }

    console.log("Mole-IA System Online.");
    // Inicializar mapa de focos si Leaflet está disponible
    if (typeof L !== 'undefined') {
        try { initMoleMap(); loadMoleMapMarkers(); } catch (e) { console.warn('Mapa no inicializado:', e); }
    }
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
    if (!fullText) return;
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
        // Llamar directamente al backend IA (Puerto 8001) para datos de sensores
        const aiBaseUrl = window.APP_CONFIG?.AI_API_URL || 'http://127.0.0.1:8001/api/v1/';
        const response = await fetch(`${aiBaseUrl}sensors/live`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data) actualizarUI(data);
        else marcarSinDatos();
    } catch (error) {
        console.warn('Sensor fetch failed:', error.message);
        marcarSinDatos();
    }
}

function actualizarUI(data) {
    const fields = ['disp-hum', 'disp-temp', 'disp-ph', 'disp-uv', 'disp-health'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.style.color = ''; el.classList.remove('sensor-error'); }
    });

    // Campos existentes
    document.getElementById('disp-hum').innerText = (data.soil_humidity || data.humidity || "--") + "%";
    document.getElementById('disp-ph').innerText = (data.ph_level || "--");

    // NUEVOS CAMPOS - Temperatura y UV
    document.getElementById('disp-temp').innerText = (data.temperature || "--") + "\u00b0C";
    document.getElementById('disp-uv').innerText = (data.uv_index || "--");

    // Estado general
    document.getElementById('disp-health').innerText = data.status || "OK";
    const box = document.getElementById('health-box');
    box.className = (data.status === 'DANGER') ? "stat-block danger" : "stat-block";
}

function marcarSinDatos() {
    const fields = ['disp-hum', 'disp-temp', 'disp-ph', 'disp-uv'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.innerText = "--"; el.style.color = "#ff4444"; }
    });

    // Estado general
    const healthEl = document.getElementById('disp-health');
    if (healthEl) { healthEl.innerText = "OFFLINE"; healthEl.style.color = "#ff4444"; }
    const box = document.getElementById('health-box');
    if (box) box.className = "stat-block danger";
}

function cambiarPlanta(key, btn) {
    plantaActual = key;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.plant-icon').forEach(i => i.classList.remove('active'));
    const icon = document.getElementById('icon-' + key);
    if (icon) icon.classList.add('active');

    document.getElementById('disp-hum').innerText = "CARGANDO...";
    fetchSensorData();
}

// --- 5. CHAT IA ---
function abrirChat() { document.getElementById('ai-modal').style.display = 'flex'; document.getElementById('ai-input').focus(); }
function cerrarChat() { document.getElementById('ai-modal').style.display = 'none'; }

function activarCamara() {
    const cameraInput = document.getElementById('camera-input');
    if (cameraInput) cameraInput.click();
}

function removerImagen() {
    pendingImageBase64 = null;
    const previewContainer = document.getElementById('image-preview-container');
    const previewThumb = document.getElementById('image-preview-thumb');
    const cameraInput = document.getElementById('camera-input');
    if (previewContainer) previewContainer.style.display = 'none';
    if (previewThumb) previewThumb.src = '';
    if (cameraInput) cameraInput.value = '';
}

/**
 * Helper: preparar FormData para enviar diagnóstico al backend (incluye coords si disponibles)
 * imageFile: File object from input
 * plantId: optional
 */
async function enviarDiagnosticoConCoords(imageFile, plantId = null) {
    if (!imageFile) return;
    const form = new FormData();
    form.append('image', imageFile, imageFile.name || 'upload.jpg');
    if (plantId) form.append('plant_id', plantId);
    if (pendingImageLat !== null && pendingImageLon !== null) {
        form.append('latitude', String(pendingImageLat));
        form.append('longitude', String(pendingImageLon));
    }

    try {
        const res = await window.apiService.upload('diagnostics/', form);
        console.log('Diagnóstico enviado:', res);
        // Después de enviar, refrescar marcadores en el mapa
        if (typeof loadMoleMapMarkers === 'function') loadMoleMapMarkers();
        return res;
    } catch (e) {
        console.error('Error enviando diagnóstico:', e);
        throw e;
    }
}

async function enviarComandoAI() {
    const input = document.getElementById('ai-input');
    const chatContainer = document.getElementById('ai-chat-container');
    const question = input.value.trim();
    if (!question && !pendingImageBase64) return;

    // Construir burbuja del usuario con thumbnail si hay imagen
    let userBubbleContent = '';
    if (pendingImageBase64) {
        userBubbleContent += `<img src="${pendingImageBase64}" class="image-in-chat" alt="Imagen enviada">`;
    }
    userBubbleContent += question || '(imagen adjunta)';
    chatContainer.innerHTML += `<div class="ai-message user">${userBubbleContent}</div>`;

    // Capturar imagen pendiente y limpiar
    const imageToSend = pendingImageBase64;
    removerImagen();
    input.value = "";
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Inicializar WebSocket si no está conectado
    if (!window.apiService.isWebSocketConnected()) {
        window.apiService.initWebSocket();
    }

    // Escuchar eventos de WebSocket
    window.addEventListener('chatMessage', handleChatResponse);

    // Enviar mensaje por WebSocket (con imagen si existe)
    window.apiService.sendChatMessage(question || 'Analiza esta imagen', plantaActual, imageToSend);
}

function handleChatResponse(event) {
    const data = event.detail;
    const chatContainer = document.getElementById('ai-chat-container');

    switch (data.type) {
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


            const responseHtml = `
                <div class="ai-message bot">
                    ${formattedAnswer}
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

// --- MAPA: Leaflet integration ---
let moleMap = null;
let moleMarkersLayer = null;

function initMoleMap() {
    if (moleMap) return;
    // Default view centered on Mexico
    moleMap = L.map('mole-map', { zoomControl: true, attributionControl: false }).setView([23.6345, -102.5528], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
    }).addTo(moleMap);

    moleMarkersLayer = L.layerGroup().addTo(moleMap);
}

async function loadMoleMapMarkers() {
    if (!window.apiService) return;
    try {
        const res = await window.apiService.get('diagnosticos/geolocalizados/');
        const items = res.results || [];
        moleMarkersLayer.clearLayers();

        items.forEach(item => {
            if (!item.latitude || !item.longitude) return;
            const color = severityToColor(item.severity);
            const marker = L.circleMarker([item.latitude, item.longitude], {
                radius: 8,
                fillColor: color,
                color: '#000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.9
            });
            const popupHtml = `<b>${escapeHtml(item.condition_name || 'Sin nombre')}</b><br/>Gravedad: ${item.severity}<br/>Fecha: ${item.created_at}`;
            marker.bindPopup(popupHtml);
            marker.addTo(moleMarkersLayer);
        });
    } catch (e) {
        console.warn('No se pudieron cargar marcadores:', e);
    }
}

function severityToColor(sev) {
    switch ((sev || '').toLowerCase()) {
        case 'high': return '#ff4d4f';
        case 'critical': return '#a8071a';
        case 'medium': return '#ff8c1a';
        case 'low': return '#52c41a';
        default: return '#ff4d4f';
    }
}

function escapeHtml(unsafe) {
    return String(unsafe)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
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